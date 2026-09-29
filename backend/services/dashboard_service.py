"""
Dashboard analytics over SYNTHETIC data.

The aggregate dashboard is built from data/social_media_privacy_assessments.csv
(1,000 fictional records produced by data/generate_dataset.py) plus anonymous
aggregates of any assessments users chose to save.

Only aggregate numbers leave this module - never individual records.
"""

import csv
import os

from backend.services.questionnaire import CATEGORIES
from backend.services.scoring_engine import RISK_LEVELS

# CSV columns that describe a risky / weak practice, and the value(s) that count as "weak".
WEAKNESS_RULES = {
    "profile_visibility": ("Public profile", {"PUBLIC"}),
    "phone_public": ("Phone number public", {"YES"}),
    "email_public": ("Email public", {"YES"}),
    "birthday_public": ("Full birthday public", {"YES"}),
    "location_public": ("Location public", {"YES"}),
    "workplace_public": ("Workplace public", {"YES"}),
    "posts_public": ("Posts public by default", {"PUBLIC"}),
    "location_tagging": ("Frequent geotagging", {"ALWAYS", "OFTEN"}),
    "travel_posts": ("Travel plans posted", {"YES"}),
    "unknown_connections": ("Accepts unknown requests", {"ALWAYS", "OFTEN"}),
    "tag_review_enabled": ("Tag review disabled", {"NO", "NOT_SURE"}),
    "third_party_apps_reviewed": ("Apps never reviewed", {"NO", "NOT_SURE"}),
    "mfa_enabled": ("MFA disabled", {"NO", "NOT_SURE"}),
    "login_alerts_enabled": ("Login alerts disabled", {"NO", "NOT_SURE"}),
    "password_reuse_reported": ("Password reuse", {"YES"}),
    "suspicious_link_awareness": ("Low link awareness", {"NO"}),
    "old_posts_reviewed": ("Old posts not reviewed", {"NO"}),
    "privacy_settings_reviewed": ("Settings not reviewed in a year", {"OVER_A_YEAR", "NEVER"}),
}

# Security controls whose adoption rate is charted ("enabled" value).
CONTROL_RULES = {
    "mfa_enabled": ("MFA", "YES"),
    "login_alerts_enabled": ("Login alerts", "YES"),
    "tag_review_enabled": ("Tag review", "YES"),
    "third_party_apps_reviewed": ("Apps reviewed", "YES"),
    "old_posts_reviewed": ("Old posts reviewed", "YES"),
}

_cache = {"key": None, "stats": None}


def _histogram(scores, bucket=10):
    bins = [0] * (100 // bucket)
    for score in scores:
        bins[min(score // bucket, len(bins) - 1)] += 1
    return {"labels": [f"{i * bucket}-{i * bucket + bucket - (0 if i == len(bins) - 1 else 1)}"
                       for i in range(len(bins))], "counts": bins}


def load_dataset_stats(csv_path):
    """Compute aggregate statistics from the synthetic CSV (cached by file mtime)."""
    if not os.path.exists(csv_path):
        return None
    key = (csv_path, os.path.getmtime(csv_path))
    if _cache["key"] == key:
        return _cache["stats"]

    with open(csv_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    total = len(rows)
    if total == 0:
        return None

    scores = [int(r["risk_score"]) for r in rows]
    distribution = {level: 0 for level in RISK_LEVELS}
    for r in rows:
        distribution[r["risk_level"]] += 1

    category_avgs = {
        cat: round(sum(int(r[f"score_{cat}"]) for r in rows) / total, 1) for cat in CATEGORIES
    }

    weaknesses = sorted(
        (
            {"key": col, "label": label,
             "count": sum(1 for r in rows if r[col] in bad),
             "percent": round(100 * sum(1 for r in rows if r[col] in bad) / total, 1)}
            for col, (label, bad) in WEAKNESS_RULES.items()
        ),
        key=lambda item: item["count"],
        reverse=True,
    )

    controls = [
        {"key": col, "label": label,
         "percent_enabled": round(100 * sum(1 for r in rows if r[col] == on) / total, 1)}
        for col, (label, on) in CONTROL_RULES.items()
    ]

    footprint = [int(r["score_digital_footprint"]) for r in rows]
    stats = {
        "source": "synthetic",
        "total_records": total,
        "average_score": round(sum(scores) / total, 1),
        "risk_distribution": distribution,
        "score_histogram": _histogram(scores),
        "category_averages": category_avgs,
        "top_weaknesses": weaknesses[:10],
        "control_adoption": controls,
        "digital_footprint_histogram": _histogram(footprint, bucket=20),
    }
    _cache.update(key=key, stats=stats)
    return stats


def get_dashboard_stats(csv_path, database):
    """Combine synthetic-dataset aggregates with anonymous stored-assessment aggregates."""
    return {
        "category_labels": {key: meta["short"] for key, meta in CATEGORIES.items()},
        "synthetic": load_dataset_stats(csv_path),
        "stored_assessments": database.aggregate_stats(),
        "note": "Aggregates only. The synthetic dataset contains fictional records, not real people.",
    }
