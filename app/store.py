"""Staged GANTT-AX imports. Imported snapshots are never approved baselines."""
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from app.ganttax import normalize_project

SCHEMA = """
CREATE TABLE IF NOT EXISTS ganttax_imports (
 id VARCHAR(36) PRIMARY KEY,
 project_code VARCHAR(255),
 imported_at TIMESTAMPTZ NOT NULL,
 source_sha256 VARCHAR(64) NOT NULL,
 mapping_version VARCHAR(20) NOT NULL,
 approval_status VARCHAR(20) NOT NULL DEFAULT 'STAGED',
 raw_state JSONB NOT NULL,
 normalized_state JSONB NOT NULL
);
"""

def get_engine():
    url=os.getenv("DATABASE_URL")
    if not url: raise RuntimeError("DATABASE_URL is not configured")
    return create_engine(url, pool_pre_ping=True)

def stage_import(payload):
    normalized=normalize_project(payload)
    canonical=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    digest=hashlib.sha256(canonical.encode()).hexdigest()
    record_id=str(uuid.uuid4())
    with get_engine().begin() as conn:
        conn.execute(text(SCHEMA))
        conn.execute(text("""INSERT INTO ganttax_imports
          (id,project_code,imported_at,source_sha256,mapping_version,approval_status,raw_state,normalized_state)
          VALUES (:id,:code,:at,:digest,'1.1','STAGED',CAST(:raw AS JSONB),CAST(:norm AS JSONB))"""),
          {"id":record_id,"code":normalized["project"].get("code"),"at":datetime.now(timezone.utc),
           "digest":digest,"raw":canonical,"norm":json.dumps(normalized,ensure_ascii=False)})
    return {"import_id":record_id,"status":"STAGED","source_sha256":digest,"task_count":len(normalized["tasks"])}

def export_import(import_id):
    with get_engine().connect() as conn:
        row=conn.execute(text("SELECT raw_state FROM ganttax_imports WHERE id=:id"),{"id":import_id}).scalar_one_or_none()
    if row is None: return None
    return row if isinstance(row,dict) else json.loads(row)
