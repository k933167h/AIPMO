"""Persistent CDPF evidence repository (PostgreSQL)."""
import json
from datetime import datetime, timezone
from sqlalchemy import text
from app.store import get_engine
from .engine import Signal, EvaluateRequest, evaluate

DDL = """
CREATE TABLE IF NOT EXISTS cdpf_evidence (
 project_id VARCHAR(255) NOT NULL,
 source VARCHAR(80) NOT NULL,
 source_id VARCHAR(255) NOT NULL,
 dimension VARCHAR(80) NOT NULL,
 severity DOUBLE PRECISION NOT NULL CHECK (severity >= 0 AND severity <= 100),
 observed_at TIMESTAMPTZ NOT NULL,
 received_at TIMESTAMPTZ NOT NULL,
 PRIMARY KEY (project_id, source, source_id)
);
CREATE INDEX IF NOT EXISTS ix_cdpf_evidence_project_time
 ON cdpf_evidence(project_id, observed_at DESC);
"""
UPSERT = """
INSERT INTO cdpf_evidence(project_id,source,source_id,dimension,severity,observed_at,received_at)
VALUES (:project_id,:source,:source_id,:dimension,:severity,:observed_at,:received_at)
ON CONFLICT (project_id,source,source_id) DO UPDATE
SET dimension=EXCLUDED.dimension, severity=EXCLUDED.severity,
    observed_at=EXCLUDED.observed_at, received_at=EXCLUDED.received_at
WHERE cdpf_evidence.observed_at <= EXCLUDED.observed_at
"""
def persist(project_id: str, signals: list[Signal]):
    if not project_id.strip(): raise ValueError("project_id required")
    # Prevent older duplicate observations from replacing newer ones.
    now=datetime.now(timezone.utc)
    with get_engine().begin() as conn:
        for statement in DDL.strip().split(";"):
            if statement.strip(): conn.execute(text(statement))
        for signal in signals:
            row=signal.model_dump()
            conn.execute(text(UPSERT),dict(project_id=project_id,**row,received_at=now))
    return {"project_id":project_id,"processed":len(signals)}

def project_risk(project_id: str):
    with get_engine().begin() as conn:
        for statement in DDL.strip().split(";"):
            if statement.strip(): conn.execute(text(statement))
        rows=conn.execute(text("""
        SELECT source,source_id,dimension,severity,observed_at
        FROM cdpf_evidence WHERE project_id=:project_id
        ORDER BY observed_at DESC LIMIT 10000
        """),{"project_id":project_id}).mappings().all()
    signals=[Signal(**dict(row)) for row in rows]
    return evaluate(EvaluateRequest(project_id=project_id,signals=signals))
