"""
Findings Engine - turns risky answers into ranked, human-readable findings.

A FINDING is created for every question whose risk value is >= 0.5
(i.e. the answer was risky, "sometimes", or "not sure").

Severity = the question's potential IMPACT adjusted by how risky the answer was:

    impact HIGH   + risk >= 0.75  -> HIGH
    impact HIGH   + risk <  0.75  -> MEDIUM
    impact MEDIUM + risk >= 0.75  -> MEDIUM
    everything else               -> LOW

Findings are ranked so the most important problems appear first ("Top Risks").
Findings contain only a finding TYPE and generic text - never personal data.
"""

from backend.services.questionnaire import CATEGORIES, QUESTION_INDEX, QUESTIONS
from backend.services.scoring_engine import DEFAULT_CATEGORY_WEIGHTS

FINDING_THRESHOLD = 0.5
SEVERITY_POINTS = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

# Protective controls shown on the dashboard ("Security Controls Enabled").
# A control counts as enabled when its question produced NO finding.
SECURITY_CONTROLS = {
    "mfa_enabled": "Multi-factor authentication",
    "password_reuse": "Unique password (no reuse)",
    "password_manager_used": "Password manager",
    "login_alerts_enabled": "Login alerts",
    "recovery_info_reviewed": "Recovery info reviewed",
    "active_sessions_reviewed": "Active sessions reviewed",
    "tag_review_enabled": "Tag review",
    "follower_approval": "Follower approval",
    "third_party_apps_reviewed": "Connected apps reviewed",
    "privacy_settings_reviewed": "Privacy settings reviewed",
}


def _severity(impact, risk_value):
    if impact == "HIGH":
        return "HIGH" if risk_value >= 0.75 else "MEDIUM"
    if impact == "MEDIUM" and risk_value >= 0.75:
        return "MEDIUM"
    return "LOW"


def _answer_note(answer):
    if answer == "NOT_SURE":
        return " You answered 'Not sure' - a setting you cannot confirm should not be relied on."
    if answer in ("SOMETIMES", "OFTEN"):
        return " Reported as happening some of the time."
    return ""


def generate_privacy_findings(features, responses, category_scores=None):
    """Create a ranked list of privacy findings.

    Args:
        features: {question_id: risk_value} from extract_privacy_features().
        responses: validated answers (used only to add a 'not sure' note).
        category_scores: optional, unused in ranking but kept for API symmetry.

    Returns:
        List of finding dicts sorted most-important first. Each has:
        finding_type, category, category_name, severity, title, description, risk_value.
    """
    findings = []
    for question in QUESTIONS:
        qid = question["id"]
        risk_value = features[qid]
        if risk_value < FINDING_THRESHOLD:
            continue

        severity = _severity(question["impact"], risk_value)
        category = question["category"]
        priority = (
            SEVERITY_POINTS[severity] * 1000
            + risk_value * question["weight"] * DEFAULT_CATEGORY_WEIGHTS[category]
        )
        findings.append({
            "finding_type": qid,
            "category": category,
            "category_name": CATEGORIES[category]["name"],
            "severity": severity,
            "title": question["finding"],
            "description": question["finding"] + "." + _answer_note(responses.get(qid, "")),
            "risk_value": risk_value,
            "_priority": priority,
        })

    findings.sort(key=lambda item: item["_priority"], reverse=True)
    for item in findings:
        item.pop("_priority")
    return findings


def findings_from_types(stored_findings):
    """Rebuild full finding objects from rows stored in the database.

    The database only keeps finding_type, category, severity and description,
    so we look the title up again from the questionnaire definition.
    """
    rebuilt = []
    for row in stored_findings:
        question = QUESTION_INDEX.get(row["finding_type"])
        if not question:
            continue
        rebuilt.append({
            "finding_type": row["finding_type"],
            "category": row["category"],
            "category_name": CATEGORIES[row["category"]]["name"],
            "severity": row["severity"],
            "title": question["finding"],
            "description": row["description"],
        })
    return rebuilt


def security_controls_summary(finding_types):
    """Report which protective controls are enabled, derived from the finding types."""
    finding_set = set(finding_types)
    controls = [
        {"control": key, "label": label, "enabled": key not in finding_set}
        for key, label in SECURITY_CONTROLS.items()
    ]
    return {
        "enabled_count": sum(1 for c in controls if c["enabled"]),
        "total": len(controls),
        "controls": controls,
    }
