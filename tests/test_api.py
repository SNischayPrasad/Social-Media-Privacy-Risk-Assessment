"""
API tests (TC28, TC30 and endpoint behaviour).
"""

from backend.services.demo_profiles import DEMO_IMPROVEMENTS


def post_assessment(client, answers, store=False):
    return client.post("/api/assessment", json={"responses": answers, "store": store})


def test_questionnaire_endpoint(client):
    data = client.get("/api/questionnaire").get_json()
    assert data["total_questions"] >= 40
    assert len(data["categories"]) == 10
    first = data["categories"][0]["questions"][0]
    assert {"id", "text", "help", "options"} <= set(first)


def test_assessment_not_stored_by_default(client, demo_answers):
    response = post_assessment(client, demo_answers)
    assert response.status_code == 201
    body = response.get_json()
    assert body["stored"] is False
    assert "delete_token" not in body
    assert client.get(f"/api/assessment/{body['assessment_id']}").status_code == 404


def test_tc28_database_save_and_retrieve(client, demo_answers):
    created = post_assessment(client, demo_answers, store=True).get_json()
    assert created["stored"] is True and created["delete_token"]

    fetched = client.get(f"/api/assessment/{created['assessment_id']}")
    assert fetched.status_code == 200
    data = fetched.get_json()
    assert data["overall_score"] == created["overall_score"]
    assert data["risk_level"] == created["risk_level"]
    assert data["category_scores"] == created["category_scores"]
    assert [f["finding_type"] for f in data["findings"]] == [f["finding_type"] for f in created["findings"]]

    recs = client.get(f"/api/assessment/{created['assessment_id']}/recommendations").get_json()
    assert len(recs["recommendations"]) == len(created["recommendations"])


def test_simulate_improvement_endpoint(client, demo_answers):
    response = client.post(
        "/api/assessment/simulate-improvement",
        json={"responses": demo_answers, "changes": DEMO_IMPROVEMENTS},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["risk_reduction"] > 0
    assert data["simulated"]["overall_score"] < data["current"]["overall_score"]


def test_tc30_report_generation(client, demo_answers):
    response = client.post("/api/report", json={"responses": demo_answers})
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    html = response.get_data(as_text=True)
    for section in ("Assessment ID", "Category Scores", "Top Findings", "Security Recommendations",
                    "Priority Actions", "Privacy Checklist", "Disclaimer"):
        assert section in html
    assert "<script" not in html.lower()
    assert "script-src" not in response.headers["Content-Security-Policy"]


def test_report_via_form_post_and_download(client, demo_answers):
    import json
    response = client.post("/api/report", data={"responses_json": json.dumps(demo_answers), "download": "1"})
    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]


def test_stored_report(client, demo_answers):
    created = post_assessment(client, demo_answers, store=True).get_json()
    response = client.get(f"/api/assessment/{created['assessment_id']}/report")
    assert response.status_code == 200
    assert created["assessment_id"] in response.get_data(as_text=True)


def test_dashboard_stats(client):
    data = client.get("/api/dashboard/stats").get_json()
    assert "stored_assessments" in data
    assert len(data["category_labels"]) == 10
    if data["synthetic"]:  # present once data/generate_dataset.py has been run
        assert data["synthetic"]["total_records"] >= 1000
        assert set(data["synthetic"]["risk_distribution"]) == {"LOW", "MODERATE", "HIGH", "CRITICAL"}


def test_privacy_checklist(client):
    data = client.get("/api/privacy-checklist?findings=mfa_enabled").get_json()
    assert len(data["items"]) >= 18
    relevant = [item["item"] for item in data["items"] if item["relevant"]]
    assert relevant == ["Enable MFA"]


def test_frontend_pages_are_served(client):
    for page in ("/", "/assessment.html", "/dashboard.html", "/checklist.html"):
        assert client.get(page).status_code == 200


def test_unknown_assessment_returns_404(client):
    assert client.get("/api/assessment/" + "a" * 32).status_code == 404
