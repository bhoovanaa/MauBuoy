"""Durable audit storage for human-approved intervention decisions."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "audit_log.db"
)


def _database_path() -> Path:
    configured = os.getenv("REEFGUARDIAN_AUDIT_DB")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DATABASE_PATH


def _connect() -> sqlite3.Connection:
    database_path = _database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS intervention_decisions (
            id TEXT PRIMARY KEY,
            decision_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            analysis_timestamp TEXT NOT NULL,
            site_id TEXT NOT NULL,
            site_name TEXT NOT NULL,
            buoy_id TEXT NOT NULL,
            buoy_name TEXT NOT NULL,
            media_type TEXT NOT NULL,
            visual_condition TEXT NOT NULL,
            visual_confidence REAL NOT NULL,
            environmental_risk_score REAL NOT NULL,
            environmental_risk_level TEXT NOT NULL,
            fusion_priority TEXT NOT NULL,
            recommendation_source TEXT NOT NULL,
            ai_recommended_technique_id TEXT NOT NULL,
            ai_recommended_technique_name TEXT NOT NULL,
            selected_technique_id TEXT NOT NULL,
            selected_technique_name TEXT NOT NULL,
            selected_rank INTEGER NOT NULL,
            selection_rationale TEXT NOT NULL,
            implementation_steps_json TEXT NOT NULL,
            caveats_json TEXT NOT NULL,
            timeline TEXT NOT NULL,
            predicted_survival_rate TEXT NOT NULL,
            baseline_risk_score REAL NOT NULL,
            projected_risk_score REAL NOT NULL,
            risk_reduction_points REAL NOT NULL,
            confidence_score REAL NOT NULL,
            impact_horizon_days INTEGER NOT NULL,
            admin_name TEXT NOT NULL,
            admin_notes TEXT NOT NULL,
            decision_status TEXT NOT NULL,
            learning_status TEXT NOT NULL
        )
        """
    )
    return connection


def _public_record(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    record["implementation_steps"] = json.loads(
        record.pop("implementation_steps_json")
    )
    record["caveats"] = json.loads(record.pop("caveats_json"))
    return record


def save_intervention_decision(payload: dict[str, Any]) -> dict[str, Any]:
    """Store one confirmed decision and return the immutable audit record."""

    record = {
        **{
            key: value
            for key, value in payload.items()
            if key not in {"implementation_steps", "caveats"}
        },
        "id": f"AUD-{uuid.uuid4().hex[:12].upper()}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision_status": "confirmed",
        "learning_status": "approved_training_example",
        "implementation_steps_json": json.dumps(
            payload["implementation_steps"], ensure_ascii=False
        ),
        "caveats_json": json.dumps(payload["caveats"], ensure_ascii=False),
    }
    columns = tuple(record)
    placeholders = ", ".join("?" for _ in columns)

    with _connect() as connection:
        try:
            connection.execute(
                f"""
                INSERT INTO intervention_decisions ({", ".join(columns)})
                VALUES ({placeholders})
                """,
                tuple(record[column] for column in columns),
            )
        except sqlite3.IntegrityError:
            existing = connection.execute(
                """
                SELECT * FROM intervention_decisions
                WHERE decision_key = ?
                """,
                (record["decision_key"],),
            ).fetchone()
            if existing is None:
                raise
            return _public_record(existing)

        stored = connection.execute(
            "SELECT * FROM intervention_decisions WHERE id = ?",
            (record["id"],),
        ).fetchone()
        assert stored is not None
        return _public_record(stored)


def list_intervention_decisions(limit: int = 100) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM intervention_decisions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_public_record(row) for row in rows]


def intervention_learning_summary() -> dict[str, Any]:
    """Return aggregate priors suitable for a future reviewed learning pipeline."""

    with _connect() as connection:
        total = connection.execute(
            "SELECT COUNT(*) FROM intervention_decisions"
        ).fetchone()[0]
        rows = connection.execute(
            """
            SELECT
                selected_technique_id,
                selected_technique_name,
                COUNT(*) AS confirmation_count,
                ROUND(AVG(risk_reduction_points), 2) AS average_risk_reduction,
                ROUND(AVG(confidence_score), 3) AS average_confidence
            FROM intervention_decisions
            WHERE learning_status = 'approved_training_example'
            GROUP BY selected_technique_id, selected_technique_name
            ORDER BY confirmation_count DESC, selected_technique_name ASC
            """
        ).fetchall()
    return {
        "approved_examples": total,
        "technique_priors": [dict(row) for row in rows],
        "usage_note": (
            "Use these human-approved examples during a reviewed evaluation or "
            "retraining cycle; do not automatically retrain on live decisions."
        ),
    }
