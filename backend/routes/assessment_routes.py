"""
Assessment API routes.

    GET    /api/questionnaire                          questionnaire definition
    GET    /api/demo-profile                           fictional demo answers
    POST   /api/assessment                             run (and optionally store) an assessment
    GET    /api/assessment/<id>                        stored, minimised assessment
    GET    /api/assessment/<id>/recommendations        recommendations for a stored assessment
    DELETE /api/assessment/<id>                        delete (requires X-Delete-Token header)
    POST   /api/assessment/simulate-improvement        what-if simulation (nothing stored)
    POST   /api/report                                 printable HTML report (nothing stored)
    GET    /api/assessment/<id>/report                 printable HTML report of a stored assessment

Privacy by default: POST /api/assessment stores NOTHING unless the client
explicitly sends "store": true. Raw answers are never stored in any case.
"""

import json
import re
import secrets

from flask import Blueprint, current_app, jsonify, make_response, request

from backend.services.assessment_engine import result_from_stored, run_assessment
from backend.services.demo_profiles import DEMO_IMPROVEMENTS, DEMO_PROFILE
from backend.services.improvement_simulator import simulate_improvement
from backend.services.questionnaire import get_questionnaire
from backend.services.report_generator import render_report_html
from backend.services.scoring_engine import DEFAULT_CATEGORY_WEIGHTS
from backend.utils.security import REPORT_CSP, rate_limited
from backend.utils.validators import ValidationError

assessment_bp = Blueprint("assessment", __name__, url_prefix="/api")

ASSESSMENT_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def _db():
    return current_app.config["DB"]


def _json_body():
    """Return the parsed JSON object body or raise a 400-style ValidationError."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValidationError(["Request body must be a JSON object."])
    return body


def _check_id(assessment_id):
    if not ASSESSMENT_ID_PATTERN.match(assessment_id):
        raise ValidationError(["Invalid assessment id format."])


def _load_stored(assessment_id):
    _check_id(assessment_id)
    stored = _db().get_assessment(assessment_id)
    if stored is None:
        return None
    return result_from_stored(stored)


def _html_report_response(result, download=False):
    response = make_response(render_report_html(result))
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Content-Security-Policy"] = REPORT_CSP
    if download:
        name = f"privacy-report-{result['assessment_id'][:8]}.html"
        response.headers["Content-Disposition"] = f'attachment; filename="{name}"'
    return response


@assessment_bp.get("/questionnaire")
def questionnaire():
    data = get_questionnaire()
    for category in data["categories"]:
        category["weight"] = DEFAULT_CATEGORY_WEIGHTS[category["key"]]
    return jsonify(data)


@assessment_bp.get("/demo-profile")
def demo_profile():
    """Answers of the FICTIONAL demo profile, used by the 'Use demo answers' button."""
    return jsonify(
        note="Fictional demonstration profile - not a real person.",
        responses=DEMO_PROFILE,
        suggested_improvements=DEMO_IMPROVEMENTS,
    )


@assessment_bp.post("/assessment")
@rate_limited
def create_assessment():
    body = _json_body()
    result = run_assessment(body.get("responses"))

    store = body.get("store", False) is True
    result["stored"] = store
    if store:
        # The deletion token is shown to the user ONCE; only its hash is stored.
        delete_token = secrets.token_urlsafe(24)
        _db().save_assessment(result, delete_token)
        result["delete_token"] = delete_token
    return jsonify(result), 201


@assessment_bp.get("/assessment/<assessment_id>")
def get_assessment(assessment_id):
    result = _load_stored(assessment_id)
    if result is None:
        return jsonify(error="Assessment not found."), 404
    return jsonify(result)


@assessment_bp.get("/assessment/<assessment_id>/recommendations")
def get_recommendations(assessment_id):
    result = _load_stored(assessment_id)
    if result is None:
        return jsonify(error="Assessment not found."), 404
    return jsonify(
        assessment_id=assessment_id,
        risk_level=result["risk_level"],
        recommendations=result["recommendations"],
    )


@assessment_bp.delete("/assessment/<assessment_id>")
@rate_limited
def delete_assessment(assessment_id):
    _check_id(assessment_id)
    token = request.headers.get("X-Delete-Token", "")
    if not token or len(token) > 128:
        return jsonify(error="Missing or invalid X-Delete-Token header."), 401
    if not _db().delete_assessment(assessment_id, token):
        # Same response for 'not found' and 'wrong token' so ids cannot be probed.
        return jsonify(error="Assessment not found or token invalid."), 404
    return jsonify(deleted=True, assessment_id=assessment_id)


@assessment_bp.post("/assessment/simulate-improvement")
@rate_limited
def simulate():
    body = _json_body()
    changes = body.get("changes")
    if changes is not None and not isinstance(changes, dict):
        raise ValidationError(["'changes' must be an object of {question_id: answer}."])
    result = simulate_improvement(
        body.get("responses"),
        changes=changes,
        fix_findings=body.get("fix_findings"),
    )
    return jsonify(result)


@assessment_bp.post("/report")
@rate_limited
def report_from_responses():
    """Stateless report: accepts JSON {"responses": {...}} or a form field responses_json."""
    if request.is_json:
        body = _json_body()
        responses = body.get("responses")
        download = body.get("download") is True
    else:
        try:
            responses = json.loads(request.form.get("responses_json", ""))
        except (TypeError, ValueError):
            raise ValidationError(["responses_json must contain valid JSON."])
        download = request.form.get("download") == "1"
    return _html_report_response(run_assessment(responses), download=download)


@assessment_bp.get("/assessment/<assessment_id>/report")
def stored_report(assessment_id):
    result = _load_stored(assessment_id)
    if result is None:
        return jsonify(error="Assessment not found."), 404
    return _html_report_response(result, download=request.args.get("download") == "1")
