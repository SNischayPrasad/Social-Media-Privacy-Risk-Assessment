"""
Functional tests TC01 - TC27: questionnaire, feature extraction, scoring,
findings, recommendations and the improvement simulator.

Each test isolates one privacy weakness by starting from a fully private
profile and changing only the answer(s) under test.
"""

import pytest

from backend.services.assessment_engine import extract_privacy_features, run_assessment
from backend.services.improvement_simulator import simulate_improvement
from backend.services.questionnaire import QUESTIONS
from backend.services.scoring_engine import (
    DEFAULT_CATEGORY_WEIGHTS,
    calculate_category_scores,
    calculate_privacy_risk,
    classify_risk,
)
from backend.services.demo_profiles import DEMO_IMPROVEMENTS
from backend.utils.validators import ValidationError
from tests.conftest import profile_with


def finding_types(result):
    return {f["finding_type"]: f for f in result["findings"]}


def rec_for(result, finding_type):
    return next(r for r in result["recommendations"] if r["finding_type"] == finding_type)


# ------------------------------------------------------------------ baseline
def test_tc00_questionnaire_has_40_plus_questions_in_10_categories():
    assert len(QUESTIONS) >= 40
    assert len({q["category"] for q in QUESTIONS}) == 10
    assert sum(DEFAULT_CATEGORY_WEIGHTS.values()) == 100


def test_tc01_fully_private_profile(private_answers):
    result = run_assessment(private_answers)
    assert result["overall_score"] == 0
    assert result["risk_level"] == "LOW"
    assert result["findings"] == []
    assert result["security_controls"]["enabled_count"] == result["security_controls"]["total"]


def test_tc02_fully_public_profile(public_answers):
    result = run_assessment(public_answers)
    assert result["overall_score"] == 100
    assert result["risk_level"] == "CRITICAL"
    assert all(score == 100 for score in result["category_scores"].values())
    assert len(result["findings"]) == len(QUESTIONS)


# ------------------------------------------------------------------ single weaknesses
def test_tc03_public_phone():
    result = run_assessment(profile_with(phone_public="YES"))
    assert result["category_scores"]["personal_information"] > 0
    finding = finding_types(result)["phone_public"]
    assert finding["severity"] == "HIGH"
    assert rec_for(result, "phone_public")["priority"] == "IMMEDIATE"


def test_tc04_public_email():
    result = run_assessment(profile_with(email_public="YES"))
    assert "email_public" in finding_types(result)
    assert result["category_scores"]["personal_information"] > 0


def test_tc05_public_birthday():
    result = run_assessment(profile_with(birthday_public="YES"))
    assert finding_types(result)["birthday_public"]["severity"] == "MEDIUM"


def test_tc06_public_location():
    result = run_assessment(profile_with(location_public="YES"))
    assert "location_public" in finding_types(result)
    assert result["category_scores"]["location_exposure"] > 0


def test_tc07_realtime_checkins():
    result = run_assessment(profile_with(realtime_checkins="ALWAYS", realtime_location_sharing="YES"))
    findings = finding_types(result)
    assert findings["realtime_checkins"]["severity"] == "HIGH"
    assert findings["realtime_location_sharing"]["severity"] == "HIGH"


def test_tc08_travel_plans():
    result = run_assessment(profile_with(travel_posts="YES"))
    assert finding_types(result)["travel_posts"]["severity"] == "HIGH"


def test_tc09_workplace_exposure():
    result = run_assessment(profile_with(workplace_public="YES"))
    assert "workplace_public" in finding_types(result)


def test_tc10_education_exposure():
    result = run_assessment(profile_with(education_public="YES"))
    assert finding_types(result)["education_public"]["severity"] == "LOW"
    assert rec_for(result, "education_public")["priority"] == "GOOD_PRACTICE"


def test_tc11_public_posts():
    public = run_assessment(profile_with(posts_visibility="PUBLIC"))
    friends = run_assessment(profile_with(posts_visibility="FRIENDS"))
    assert public["category_scores"]["content_exposure"] > friends["category_scores"]["content_exposure"] > 0


def test_tc12_unknown_connections():
    result = run_assessment(profile_with(unknown_connections="ALWAYS"))
    assert finding_types(result)["unknown_connections"]["severity"] == "HIGH"
    assert result["category_scores"]["connection_risk"] > 0


def test_tc13_tag_review_disabled():
    result = run_assessment(profile_with(tag_review_enabled="NO"))
    assert "tag_review_enabled" in finding_types(result)
    assert result["category_scores"]["tagging_risk"] == round(100 * 3.0 / 7.5)


def test_tc14_mfa_disabled():
    result = run_assessment(profile_with(mfa_enabled="NO"))
    assert finding_types(result)["mfa_enabled"]["severity"] == "HIGH"
    assert rec_for(result, "mfa_enabled")["priority"] == "IMMEDIATE"
    mfa = next(c for c in result["security_controls"]["controls"] if c["control"] == "mfa_enabled")
    assert mfa["enabled"] is False


def test_tc15_login_alerts_disabled():
    result = run_assessment(profile_with(login_alerts_enabled="NO"))
    assert "login_alerts_enabled" in finding_types(result)


def test_tc16_password_reuse_reported():
    result = run_assessment(profile_with(password_reuse="YES"))
    assert rec_for(result, "password_reuse")["priority"] == "IMMEDIATE"


def test_tc17_third_party_apps_not_reviewed():
    result = run_assessment(profile_with(third_party_apps_reviewed="NO"))
    assert "third_party_apps_reviewed" in finding_types(result)
    assert result["category_scores"]["third_party_apps"] > 0


def test_tc18_low_suspicious_link_awareness():
    result = run_assessment(profile_with(suspicious_link_awareness="NO"))
    assert finding_types(result)["suspicious_link_awareness"]["severity"] == "HIGH"


def test_tc19_old_posts_not_reviewed():
    result = run_assessment(profile_with(old_posts_reviewed="NO"))
    assert "old_posts_reviewed" in finding_types(result)
    assert result["category_scores"]["digital_footprint"] > 0


def test_tc20_privacy_settings_not_reviewed():
    never = run_assessment(profile_with(privacy_settings_reviewed="NEVER"))
    recent = run_assessment(profile_with(privacy_settings_reviewed="WITHIN_YEAR"))
    assert "privacy_settings_reviewed" in finding_types(never)
    assert "privacy_settings_reviewed" not in finding_types(recent)  # 0.3 is below the threshold


def test_not_sure_is_treated_as_moderate_risk():
    result = run_assessment(profile_with(mfa_enabled="NOT_SURE"))
    finding = finding_types(result)["mfa_enabled"]
    assert "Not sure" in finding["description"]


# ------------------------------------------------------------------ calculations
def test_tc21_category_score_calculation():
    # Personal information weights: 3 + 2 + 2.5 + 3 + 1.5 + 1 + 1.5 = 14.5
    features = extract_privacy_features(profile_with(phone_public="YES"))["features"]
    scores = calculate_category_scores(features)
    assert scores["personal_information"] == round(100 * 3.0 / 14.5)  # 21
    assert all(score == 0 for key, score in scores.items() if key != "personal_information")


def test_tc22_overall_score_calculation():
    category_scores = {key: 0 for key in DEFAULT_CATEGORY_WEIGHTS}
    category_scores["account_security"] = 100      # weight 15
    category_scores["location_exposure"] = 60      # weight 15
    result = calculate_privacy_risk(category_scores)
    assert result["overall_score"] == round((15 * 100 + 15 * 60) / 100)  # 24
    assert result["risk_level"] == "MODERATE"
    assert result["high_risk_categories"] == ["account_security", "location_exposure"]


def test_custom_weights_change_the_overall_score():
    category_scores = {key: 0 for key in DEFAULT_CATEGORY_WEIGHTS}
    category_scores["account_security"] = 100
    only_security = calculate_privacy_risk(category_scores, weights={"account_security": 1})
    assert only_security["overall_score"] == 100
    with pytest.raises(ValueError):
        calculate_privacy_risk(category_scores, weights={"not_a_category": 5})
    with pytest.raises(ValueError):
        calculate_privacy_risk(category_scores, weights={"account_security": -1})


@pytest.mark.parametrize("score,level", [(0, "LOW"), (20, "LOW"), (21, "MODERATE")])
def test_tc23_score_boundary_20(score, level):
    assert classify_risk(score) == level


@pytest.mark.parametrize("score,level", [(40, "MODERATE"), (41, "HIGH")])
def test_tc24_score_boundary_40(score, level):
    assert classify_risk(score) == level


@pytest.mark.parametrize("score,level", [(70, "HIGH"), (71, "CRITICAL"), (100, "CRITICAL")])
def test_tc25_score_boundary_70(score, level):
    assert classify_risk(score) == level


# ------------------------------------------------------------------ recommendations & simulation
def test_tc26_recommendation_generation(demo_answers):
    result = run_assessment(demo_answers)
    recs = result["recommendations"]
    assert len(recs) == len(result["findings"])            # personalised: one per finding
    order = ["IMMEDIATE", "IMPORTANT", "GOOD_PRACTICE"]
    priorities = [order.index(r["priority"]) for r in recs]
    assert priorities == sorted(priorities)                 # prioritised
    assert all(r["recommendation"] and r["why"] for r in recs)


def test_tc27_improvement_simulation(demo_answers):
    sim = simulate_improvement(demo_answers, changes=DEMO_IMPROVEMENTS)
    assert sim["simulated"]["overall_score"] < sim["current"]["overall_score"]
    assert sim["risk_reduction"] == sim["current"]["overall_score"] - sim["simulated"]["overall_score"]
    assert len(sim["changes_applied"]) == len(DEMO_IMPROVEMENTS)
    assert "not a guarantee" in sim["disclaimer"]

    everything = simulate_improvement(demo_answers, fix_findings="ALL")
    assert everything["simulated"]["risk_level"] == "LOW"


def test_simulation_rejects_invalid_changes(demo_answers):
    with pytest.raises(ValidationError):
        simulate_improvement(demo_answers, changes={"mfa_enabled": "MAYBE"})
    with pytest.raises(ValidationError):
        simulate_improvement(demo_answers, fix_findings=["does_not_exist"])
