"""
Assessment Engine - privacy feature extraction and orchestration.

Pipeline (see docs/04_ARCHITECTURE_API_DATABASE.md):

    responses -> validate -> extract_privacy_features -> category scores
              -> overall risk -> findings -> recommendations -> result

`run_assessment()` is the one function the API calls. It is a pure function:
it does not touch the database, so it is easy to test and re-use (the
improvement simulator and the dataset generator call it too).
"""

import uuid
from datetime import datetime, timezone

from backend.services.questionnaire import CATEGORIES, QUESTIONS, QUESTION_INDEX, answer_risk
from backend.services.scoring_engine import calculate_category_scores, calculate_privacy_risk
from backend.services.findings_engine import (
    findings_from_types,
    generate_privacy_findings,
    security_controls_summary,
)
from backend.services.recommendation_engine import generate_recommendations
from backend.utils.validators import validate_responses

DISCLAIMER = (
    "This is an educational privacy-risk framework based on self-reported answers. "
    "Scores, weights and thresholds are teaching assumptions, not a validated risk model. "
    "A low score does not guarantee an account is safe, and a high score does not mean it "
    "will be compromised."
)


def extract_privacy_features(responses):
    """Convert validated questionnaire answers into numerical risk features.

    Each feature is a float between 0.0 (no added exposure) and 1.0 (maximum
    added exposure). For example:

        phone_public = "YES"        -> {"phone_public": 1.0}   high exposure contribution
        mfa_enabled  = "NO"         -> {"mfa_enabled": 1.0}    account-security risk
        tag_review_enabled = "YES"  -> {"tag_review_enabled": 0.0}

    Returns:
        dict with:
            "features":    {question_id: risk_value}
            "by_category": {category_key: {question_id: risk_value}}
    """
    features = {}
    by_category = {key: {} for key in CATEGORIES}

    for question in QUESTIONS:
        qid = question["id"]
        value = answer_risk(qid, responses[qid])
        features[qid] = value
        by_category[question["category"]][qid] = value

    return {"features": features, "by_category": by_category}


def run_assessment(responses, weights=None, thresholds=None, assessment_id=None):
    """Run the full privacy assessment on a set of questionnaire responses.

    Args:
        responses: dict {question_id: answer_code} (validated here).
        weights: optional custom category weights (see scoring_engine).
        thresholds: optional custom risk-level thresholds.
        assessment_id: optional id; a random UUID is generated when omitted.

    Returns:
        A JSON-serialisable result dictionary. It contains NO raw answers and no
        personal data - only scores, finding types and recommendations.
    """
    clean = validate_responses(responses)
    extracted = extract_privacy_features(clean)

    category_scores = calculate_category_scores(extracted["features"])
    overall = calculate_privacy_risk(category_scores, weights=weights, thresholds=thresholds)
    findings = generate_privacy_findings(extracted["features"], clean, category_scores)
    recommendations = generate_recommendations(findings)

    return {
        "assessment_id": assessment_id or uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_score": overall["overall_score"],
        "risk_level": overall["risk_level"],
        "weights_used": overall["weights"],
        "category_scores": category_scores,
        "category_levels": overall["category_levels"],
        "high_risk_categories": overall["high_risk_categories"],
        "findings": findings,
        "top_findings": findings[:5],
        "recommendations": recommendations,
        "security_controls": security_controls_summary([f["finding_type"] for f in findings]),
        "question_count": len(QUESTION_INDEX),
        "disclaimer": DISCLAIMER,
    }


def result_from_stored(stored):
    """Rebuild a full result object from the minimised database record.

    Only scores and finding types are stored, so recommendations, levels and
    control summaries are re-derived here from the static catalogs.
    """
    findings = findings_from_types(stored["findings"])
    derived = calculate_privacy_risk(stored["category_scores"])
    return {
        "assessment_id": stored["assessment_id"],
        "created_at": stored["created_at"],
        "overall_score": stored["overall_score"],
        "risk_level": stored["risk_level"],
        "category_scores": {key: stored["category_scores"].get(key, 0) for key in CATEGORIES},
        "category_levels": derived["category_levels"],
        "high_risk_categories": derived["high_risk_categories"],
        "findings": findings,
        "top_findings": findings[:5],
        "recommendations": generate_recommendations(findings),
        "security_controls": security_controls_summary([f["finding_type"] for f in findings]),
        "question_count": len(QUESTION_INDEX),
        "disclaimer": DISCLAIMER,
    }
