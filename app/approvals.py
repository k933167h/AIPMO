"""Persisted baseline proposal and reviewer approval.

Approval is server-side and immutable after approval; project access controls
are still single-tenant API-key only and must be extended before production.
"""
import json
import uuid
from datetime import datetime,timezone
from sqlalchemy import text
from app.store import get_engine

SCHEMA="""
CREATE TABLE IF NOT EXISTS pmo_baselines (
 id VARCHAR(36) PRIMARY KEY,
 project_code VARCHAR(255) NOT NULL,
 approval_status VARCHAR(20) NOT NULL,
 created_at TIMESTAMPTZ NOT NULL,
 approved_at TIMESTAMPTZ,
 approved_by VARCHAR(255),
 baseline_state JSONB NOT NULL
);
"""

def propose_baseline(project_code,baseline):
    if not project_code or not isinstance(baseline,dict) or not isinstance(baseline.get("tasks"),list):
        raise ValueError("project code and baseline tasks required")
    identifier=str(uuid.uuid4())
    with get_engine().begin() as conn:
        conn.execute(text(SCHEMA))
        conn.execute(text("""INSERT INTO pmo_baselines(id,project_code,approval_status,created_at,baseline_state)
                            VALUES (:id,:code,'STAGED',:created,CAST(:state AS JSONB))"""),
                     {"id":identifier,"code":project_code,"created":datetime.now(timezone.utc),
                      "state":json.dumps(baseline,ensure_ascii=False)})
    return {"baseline_id":identifier,"approval_status":"STAGED"}

def approve_baseline(baseline_id,reviewer):
    if not reviewer or not reviewer.strip():
        raise ValueError("reviewer identity required")
    with get_engine().begin() as conn:
        conn.execute(text(SCHEMA))
        row=conn.execute(text("""UPDATE pmo_baselines SET approval_status='APPROVED',
            approved_at=:now,approved_by=:reviewer WHERE id=:id AND approval_status='STAGED'
            RETURNING id,project_code,approved_by"""),
            {"now":datetime.now(timezone.utc),"reviewer":reviewer.strip(),"id":baseline_id}).mappings().first()
    if row is None: return None
    return {"baseline_id":row["id"],"project_code":row["project_code"],
            "approval_status":"APPROVED","approved_by":row["approved_by"]}

def load_approved_baseline(baseline_id):
    with get_engine().connect() as conn:
        row=conn.execute(text("""SELECT baseline_state FROM pmo_baselines
             WHERE id=:id AND approval_status='APPROVED'"""),{"id":baseline_id}).scalar_one_or_none()
    if row is None: return None
    baseline=row if isinstance(row,dict) else json.loads(row)
    return {**baseline,"id":baseline_id,"approval_status":"APPROVED"}
