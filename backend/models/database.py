"""
Privacy-first SQLite storage.

WHAT WE STORE (data minimisation)
    ASSESSMENTS      assessment_id, overall_score, risk_level, created_at,
                     delete_token_hash (SHA-256 of a random deletion token)
    CATEGORY_SCORES  category_score_id, assessment_id, category, score
    FINDINGS         finding_id, assessment_id, category, finding_type, severity, description
    RECOMMENDATIONS  recommendation_id, finding_type, recommendation, priority  (static catalog)

WHAT WE NEVER STORE
    raw questionnaire answers, phone numbers, email addresses, home addresses,
    birth dates, passwords, exact locations, private messages, IP addresses,
    names or usernames.

RETENTION
    Assessments older than RETENTION_DAYS are purged on start-up
    (retention limitation). Users can delete their own assessment at any time
    with the deletion token they received (user control).

All queries use parameterised SQL ("?" placeholders) to prevent SQL injection.
"""

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from backend.services.recommendation_engine import catalog_rows

SCHEMA = """
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id      TEXT PRIMARY KEY,
    overall_score      INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    risk_level         TEXT    NOT NULL CHECK (risk_level IN ('LOW','MODERATE','HIGH','CRITICAL')),
    created_at         TEXT    NOT NULL,
    delete_token_hash  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS category_scores (
    category_score_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id      TEXT    NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    category           TEXT    NOT NULL,
    score              INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS findings (
    finding_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id      TEXT    NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    category           TEXT    NOT NULL,
    finding_type       TEXT    NOT NULL,
    severity           TEXT    NOT NULL CHECK (severity IN ('HIGH','MEDIUM','LOW')),
    description        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_type       TEXT    NOT NULL UNIQUE,
    recommendation     TEXT    NOT NULL,
    priority           TEXT    NOT NULL CHECK (priority IN ('IMMEDIATE','IMPORTANT','GOOD_PRACTICE'))
);

CREATE INDEX IF NOT EXISTS idx_category_scores_assessment ON category_scores(assessment_id);
CREATE INDEX IF NOT EXISTS idx_findings_assessment ON findings(assessment_id);
"""


def hash_token(token):
    """One-way hash of the deletion token. The plain token is never stored."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class Database:
    """Tiny data-access layer around SQLite."""

    def __init__(self, path):
        self.path = path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------ setup
    def init_schema(self):
        """Create tables (idempotent) and seed the static recommendation catalog."""
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT OR REPLACE INTO recommendations (finding_type, recommendation, priority) "
                "VALUES (?, ?, ?)",
                catalog_rows(),
            )

    # ------------------------------------------------------------------ write
    def save_assessment(self, result, delete_token):
        """Persist ONLY the minimised result fields. Raw answers are never passed in."""
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO assessments (assessment_id, overall_score, risk_level, created_at, "
                "delete_token_hash) VALUES (?, ?, ?, ?, ?)",
                (result["assessment_id"], result["overall_score"], result["risk_level"],
                 result["created_at"], hash_token(delete_token)),
            )
            conn.executemany(
                "INSERT INTO category_scores (assessment_id, category, score) VALUES (?, ?, ?)",
                [(result["assessment_id"], cat, score) for cat, score in result["category_scores"].items()],
            )
            conn.executemany(
                "INSERT INTO findings (assessment_id, category, finding_type, severity, description) "
                "VALUES (?, ?, ?, ?, ?)",
                [(result["assessment_id"], f["category"], f["finding_type"], f["severity"], f["description"])
                 for f in result["findings"]],
            )

    def delete_assessment(self, assessment_id, delete_token):
        """Delete an assessment if the token matches. Returns True when a row was deleted."""
        with self.connect() as conn:
            cursor = conn.execute(
                "DELETE FROM assessments WHERE assessment_id = ? AND delete_token_hash = ?",
                (assessment_id, hash_token(delete_token)),
            )
            return cursor.rowcount > 0

    def purge_older_than(self, days):
        """Retention limitation: remove assessments older than `days` days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM assessments WHERE created_at < ?", (cutoff,))
            return cursor.rowcount

    # ------------------------------------------------------------------ read
    def assessment_exists(self, assessment_id):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM assessments WHERE assessment_id = ?", (assessment_id,)
            ).fetchone()
            return row is not None

    def get_assessment(self, assessment_id):
        """Return the stored (minimised) assessment or None."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT assessment_id, overall_score, risk_level, created_at "
                "FROM assessments WHERE assessment_id = ?",
                (assessment_id,),
            ).fetchone()
            if row is None:
                return None
            scores = conn.execute(
                "SELECT category, score FROM category_scores WHERE assessment_id = ?",
                (assessment_id,),
            ).fetchall()
            findings = conn.execute(
                "SELECT category, finding_type, severity, description FROM findings "
                "WHERE assessment_id = ? ORDER BY finding_id",
                (assessment_id,),
            ).fetchall()
        return {
            **dict(row),
            "category_scores": {r["category"]: r["score"] for r in scores},
            "findings": [dict(f) for f in findings],
        }

    def get_recommendation_catalog(self):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT finding_type, recommendation, priority FROM recommendations"
            ).fetchall()
        return {r["finding_type"]: dict(r) for r in rows}

    def aggregate_stats(self):
        """Anonymous aggregates over stored assessments (no per-person data)."""
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]
            levels = conn.execute(
                "SELECT risk_level, COUNT(*) AS n FROM assessments GROUP BY risk_level"
            ).fetchall()
            avg = conn.execute("SELECT AVG(overall_score) FROM assessments").fetchone()[0]
            top = conn.execute(
                "SELECT finding_type, COUNT(*) AS n FROM findings GROUP BY finding_type "
                "ORDER BY n DESC LIMIT 10"
            ).fetchall()
        return {
            "total": total,
            "average_score": round(avg, 1) if avg is not None else None,
            "risk_distribution": {r["risk_level"]: r["n"] for r in levels},
            "top_finding_types": {r["finding_type"]: r["n"] for r in top},
        }

    def table_columns(self):
        """Used by privacy tests to prove no sensitive columns exist."""
        with self.connect() as conn:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )]
            return {
                table: [col[1] for col in conn.execute(f"PRAGMA table_info({table})")]
                for table in tables
            }
