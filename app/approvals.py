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

AUDIT_SCHEMA="""
CREATE TABLE IF NOT EXISTS pmo_baseline_audit (
 id VARCHAR(36) PRIMARY KEY,
 baseline_id VARCHAR(36) NOT NULL,
 action VARCHAR(32) NOT NULL,
 actor VARCHAR(255) NOT NULL,
 occurred_at TIMESTAMPTZ NOT NULL
);
"""
def _audit(conn,baseline_id,action,actor):
    conn.execute(text(AUDIT_SCHEMA))
    conn.execute(text("""INSERT INTO pmo_baseline_audit(id,baseline_id,action,actor,occurred_at)
        VALUES (:id,:baseline_id,:action,:actor,:occurred_at)"""),
        {"id":str(uuid.uuid4()),"baseline_id":baseline_id,"action":action,
         "actor":actor,"occurred_at":datetime.now(timezone.utc)})

def audit_events(baseline_id):
    with get_engine().begin() as conn:
        conn.execute(text(AUDIT_SCHEMA))
        rows=conn.execute(text("""SELECT action,actor,occurred_at FROM pmo_baseline_audit
            WHERE baseline_id=:id ORDER BY occurred_at,id"""),{"id":baseline_id}).mappings().all()
    return [{"action":r["action"],"actor":r["actor"],
             "occurred_at":r["occurred_at"].isoformat()} for r in rows]

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
        _audit(conn,identifier,"PROPOSED","system")
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
        if row is not None: _audit(conn,baseline_id,"APPROVED",reviewer.strip())
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
