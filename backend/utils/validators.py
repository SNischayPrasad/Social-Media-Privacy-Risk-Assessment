"""
Input validation for questionnaire responses.

Security principle: NEVER trust input from the client. Every response is
checked against an allow-list built from the questionnaire definition:

    * the payload must be a JSON object (dict)
    * every key must be a known question id  (unknown keys are rejected)
    * every value must be one of that question's allowed answer codes
    * all questions must be answered (unless partial answers are allowed)

Because only fixed answer codes such as "YES" or "PUBLIC" are accepted,
free text (and therefore personal data or script payloads) can never enter
the scoring engine, the database or the report.
"""

from backend.services.questionnaire import QUESTION_INDEX, QUESTIONS

MAX_KEY_LENGTH = 64
MAX_VALUE_LENGTH = 32


class ValidationError(ValueError):
    """Raised when questionnaire input is invalid. Carries a list of messages."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_responses(responses, allow_partial=False):
    """Validate and normalise questionnaire answers.

    Args:
        responses: dict of {question_id: answer_code}.
        allow_partial: if True, missing questions are allowed (used by the simulator
            for the 'changes' dictionary).

    Returns:
        A new dict with upper-cased, validated answers.

    Raises:
        ValidationError: with a list of human-readable error messages.
    """
    if not isinstance(responses, dict):
        raise ValidationError(["Responses must be a JSON object of {question_id: answer}."])

    errors = []
    clean = {}

    for key, value in responses.items():
        if not isinstance(key, str) or len(key) > MAX_KEY_LENGTH:
            errors.append("Invalid question id.")
            continue
        if key not in QUESTION_INDEX:
            # Do not echo long / arbitrary input back; the length check above bounds it.
            errors.append(f"Unknown question id: '{key}'.")
            continue
        if not isinstance(value, str) or len(value) > MAX_VALUE_LENGTH:
            errors.append(f"Answer for '{key}' must be a short text code.")
            continue

        answer = value.strip().upper()
        allowed = QUESTION_INDEX[key]["options"]
        if answer not in allowed:
            errors.append(f"Invalid answer for '{key}'. Allowed: {', '.join(allowed)}.")
            continue
        clean[key] = answer

    if not allow_partial:
        missing = [q["id"] for q in QUESTIONS if q["id"] not in responses]
        if missing:
            errors.append(f"{len(missing)} question(s) not answered: {', '.join(missing)}.")

    if errors:
        raise ValidationError(errors)
    return clean
