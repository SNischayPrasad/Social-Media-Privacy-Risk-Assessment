"""
Security & privacy tests (TC29 and section 34 of the brief).

These tests prove the application:
    * does not store phone numbers, emails, addresses, birth dates, passwords,
      exact locations, private messages or raw answers
    * validates input strictly (allow-list)
    * escapes output (XSS protection)
    * rate-limits POST endpoints
    * sends security headers
    * reads configuration from environment variables
    * lets users delete their data, and enforces retention
"""

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from backend.app import create_app
from backend.config import TestConfig
from backend.services.assessment_engine import run_assessment
from backend.services.report_generator import render_report_html
from backend.utils.security import rate_limiter
from backend.utils.validators import ValidationError, validate_responses

SENSITIVE_WORDS = ("phone_number", "email_address", "address", "birth", "dob", "password",
                   "latitude", "longitude", "gps", "message", "name", "username", "ip",
                   "answer", "response")

ALLOWED_COLUMNS = {
    "assessments": {"assessment_id", "overall_score", "risk_level", "created_at", "delete_token_hash"},
    "category_scores": {"category_score_id", "assessment_id", "category", "score"},
    "findings": {"finding_id", "assessment_id", "category", "finding_type", "severity", "description"},
    "recommendations": {"recommendation_id", "finding_type", "recommendation", "priority"},
}


# ------------------------------------------------------------------ data minimisation
def test_tc29_sensitive_data_not_stored(app, client, demo_answers):
    created = client.post("/api/assessment", json={"responses": demo_answers, "store": True}).get_json()
    db = app.config["DB"]

    # 1. Schema contains only the approved, non-sensitive columns.
    columns = db.table_columns()
    for table, allowed in ALLOWED_COLUMNS.items():
        assert set(columns[table]) == allowed, table
    for table, cols in columns.items():
        for col in cols:
            if col in ("delete_token_hash",):
                continue
            assert not any(word == col or col.startswith(word + "_") for word in SENSITIVE_WORDS), col

    # 2. The plain deletion token is never stored, only its hash.
    with sqlite3.connect(db.path) as conn:
        dump = "\n".join(conn.iterdump())
    assert created["delete_token"] not in dump

    # 3. Raw answer codes that are not part of finding text are not stored.
    assert "'PUBLIC'" not in dump and "'OFTEN'" not in dump


def test_assessment_result_contains_no_raw_answers(demo_answers):
    result = run_assessment(demo_answers)
    assert "responses" not in result
    assert "answers" not in result
    assert "features" not in result


def test_stored_data_can_be_deleted(client, demo_answers):
    created = client.post("/api/assessment", json={"responses": demo_answers, "store": True}).get_json()
    url = f"/api/assessment/{created['assessment_id']}"

    assert client.delete(url).status_code == 401                                        # no token
    assert client.delete(url, headers={"X-Delete-Token": "wrong"}).status_code == 404   # wrong token
    ok = client.delete(url, headers={"X-Delete-Token": created["delete_token"]})
    assert ok.status_code == 200 and ok.get_json()["deleted"] is True
    assert client.get(url).status_code == 404                                           # really gone


def test_retention_policy_purges_old_assessments(app, demo_answers):
    db = app.config["DB"]
    result = run_assessment(demo_answers)
    result["created_at"] = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(timespec="seconds")
    db.save_assessment(result, "token")
    assert db.purge_older_than(30) == 1
    assert db.get_assessment(result["assessment_id"]) is None


# ------------------------------------------------------------------ input validation
def test_validation_rejects_missing_answers(private_answers):
    private_answers.pop("mfa_enabled")
    with pytest.raises(ValidationError) as error:
        validate_responses(private_answers)
    assert "mfa_enabled" in str(error.value)


def test_validation_rejects_unknown_questions_and_free_text(private_answers):
    with pytest.raises(ValidationError):
        validate_responses({**private_answers, "phone_number": "+1 555 0100"})
    with pytest.raises(ValidationError):
        validate_responses({**private_answers, "phone_public": "+1 555 0100"})
    with pytest.raises(ValidationError):
        validate_responses({**private_answers, "phone_public": 1})
    with pytest.raises(ValidationError):
        validate_responses(["not", "a", "dict"])


def test_validation_normalises_case(private_answers):
    private_answers["mfa_enabled"] = " yes "
    assert validate_responses(private_answers)["mfa_enabled"] == "YES"


def test_api_returns_400_for_invalid_input(client, private_answers):
    assert client.post("/api/assessment", data="not json", content_type="application/json").status_code == 400
    assert client.post("/api/assessment", json=["list"]).status_code == 400
    bad = {**private_answers, "mfa_enabled": "<script>alert(1)</script>"}
    response = client.post("/api/assessment", json={"responses": bad})
    assert response.status_code == 400
    assert response.mimetype == "application/json"
    assert "<script>" not in response.get_data(as_text=True)   # long/malicious values are not echoed


def test_invalid_assessment_id_is_rejected(client):
    assert client.get("/api/assessment/../../etc/passwd").status_code == 404
    assert client.get("/api/assessment/not-a-valid-id").status_code == 400


def test_oversized_request_rejected(client):
    huge = {"responses": {"x" * 10: "y" * 40_000}}
    assert client.post("/api/assessment", json=huge).status_code == 413


# ------------------------------------------------------------------ XSS
def test_report_escapes_html(demo_answers):
    result = run_assessment(demo_answers)
    result["assessment_id"] = '"><script>alert("x")</script>'
    result["findings"][0]["title"] = "<img src=x onerror=alert(1)>"
    html = render_report_html(result)
    assert "<script>alert" not in html
    assert "<img src=x" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


# ------------------------------------------------------------------ headers & rate limiting
def test_security_headers_present(client):
    response = client.get("/api/questionnaire")
    headers = response.headers
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["Cache-Control"] == "no-store"
    assert "geolocation=()" in headers["Permissions-Policy"]


def test_rate_limiting(tmp_path, private_answers):
    rate_limiter.reset()
    app = create_app(TestConfig, overrides={"DATABASE_PATH": str(tmp_path / "rl.db"),
                                            "RATE_LIMIT_PER_MINUTE": 3})
    client = app.test_client()
    codes = [client.post("/api/assessment", json={"responses": private_answers}).status_code
             for _ in range(4)]
    assert codes == [201, 201, 201, 429]
    rate_limiter.reset()


def test_errors_do_not_leak_stack_traces(client):
    response = client.post("/api/assessment/simulate-improvement", json={"responses": {}, "changes": "x"})
    assert response.status_code == 400
    assert "Traceback" not in response.get_data(as_text=True)


# ------------------------------------------------------------------ configuration
def test_configuration_comes_from_environment(monkeypatch):
    import importlib

    import backend.config as config_module

    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "7")
    monkeypatch.setenv("FLASK_DEBUG", "false")
    reloaded = importlib.reload(config_module)
    assert reloaded.Config.RATE_LIMIT_PER_MINUTE == 7
    assert reloaded.Config.DEBUG is False
    assert reloaded.Config.HOST == "127.0.0.1"
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE")
    importlib.reload(config_module)
