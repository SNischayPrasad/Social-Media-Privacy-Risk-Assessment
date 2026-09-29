"""
Dashboard and checklist API routes.

    GET /api/dashboard/stats      aggregate statistics (synthetic dataset + anonymous stored aggregates)
    GET /api/privacy-checklist    the privacy checklist (?findings=a,b highlights relevant items)
    GET /api/health               simple liveness check
"""

import re

from flask import Blueprint, current_app, jsonify, request

from backend.services.checklist import get_checklist
from backend.services.dashboard_service import get_dashboard_stats

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")

FINDING_ID_PATTERN = re.compile(r"^[a-z_]{1,64}$")


@dashboard_bp.get("/dashboard/stats")
def dashboard_stats():
    stats = get_dashboard_stats(current_app.config["DATASET_PATH"], current_app.config["DB"])
    return jsonify(stats)


@dashboard_bp.get("/privacy-checklist")
def privacy_checklist():
    raw = request.args.get("findings", "")[:2000]
    findings = [f for f in raw.split(",") if FINDING_ID_PATTERN.match(f)]
    return jsonify(title="Social Media Privacy Checklist", items=get_checklist(findings))


@dashboard_bp.get("/health")
def health():
    return jsonify(status="ok")
