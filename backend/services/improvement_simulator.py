"""
Privacy Improvement Simulator - "What happens if I improve my settings?"

The simulator takes the user's current answers, applies a set of proposed
changes (for example "phone -> private", "MFA -> enabled"), re-runs the SAME
scoring engine, and reports the before/after difference.

Two ways to describe changes:
    1. changes = {"phone_public": "NO", "mfa_enabled": "YES"}   (explicit answers)
    2. fix_findings = ["phone_public", "mfa_enabled"] or "ALL"  (use the safest answer)

IMPORTANT: this is a FRAMEWORK SIMULATION. A lower simulated score shows the
change reduces exposure *according to this model*; it is not a guarantee of
real-world safety.
"""

from backend.services.assessment_engine import run_assessment
from backend.services.questionnaire import ANSWER_LABELS, QUESTION_INDEX, safest_answer
from backend.utils.validators import ValidationError, validate_responses

SIMULATION_DISCLAIMER = (
    "Framework simulation only: the simulated score shows how this educational model reacts to "
    "the proposed changes. It is not a guarantee of real-world privacy or account safety."
)


def _snapshot(result):
    return {
        "overall_score": result["overall_score"],
        "risk_level": result["risk_level"],
        "category_scores": result["category_scores"],
        "finding_count": len(result["findings"]),
        "security_controls_enabled": result["security_controls"]["enabled_count"],
    }


def simulate_improvement(responses, changes=None, fix_findings=None, weights=None):
    """Simulate the effect of improving privacy settings.

    Args:
        responses: complete current answers {question_id: answer}.
        changes: optional partial answers to override.
        fix_findings: optional list of question ids (or the string "ALL") to set
            to their safest answer.
        weights: optional custom category weights.

    Returns:
        dict with current, simulated, risk_reduction, changes_applied,
        category_changes and a disclaimer.
    """
    current_answers = validate_responses(responses)
    proposed = dict(current_answers)

    if changes:
        proposed.update(validate_responses(changes, allow_partial=True))

    if fix_findings:
        current_result = run_assessment(current_answers, weights=weights)
        if fix_findings == "ALL":
            targets = [f["finding_type"] for f in current_result["findings"]]
        elif isinstance(fix_findings, list):
            unknown = [t for t in fix_findings if t not in QUESTION_INDEX]
            if unknown:
                raise ValidationError([f"Unknown finding type(s): {', '.join(map(str, unknown))}."])
            targets = fix_findings
        else:
            raise ValidationError(["fix_findings must be a list of question ids or 'ALL'."])
        for qid in targets:
            proposed[qid] = safest_answer(qid)

    before = run_assessment(current_answers, weights=weights)
    after = run_assessment(proposed, weights=weights)

    changes_applied = [
        {
            "question_id": qid,
            "question": QUESTION_INDEX[qid]["text"],
            "from": ANSWER_LABELS[current_answers[qid]],
            "to": ANSWER_LABELS[proposed[qid]],
        }
        for qid in proposed
        if proposed[qid] != current_answers[qid]
    ]

    category_changes = {
        key: {
            "before": before["category_scores"][key],
            "after": after["category_scores"][key],
            "reduction": before["category_scores"][key] - after["category_scores"][key],
        }
        for key in before["category_scores"]
    }

    return {
        "current": _snapshot(before),
        "simulated": _snapshot(after),
        "risk_reduction": before["overall_score"] - after["overall_score"],
        "changes_applied": changes_applied,
        "category_changes": category_changes,
        "remaining_recommendations": after["recommendations"][:5],
        "disclaimer": SIMULATION_DISCLAIMER,
    }
