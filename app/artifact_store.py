"""PostgreSQL-backed artifact links; references only, no document payloads."""
import json
from sqlalchemy import text
from app.store import get_engine
from app.artifact_registry import stable_id

SCHEMA = """
CREATE TABLE IF NOT EXISTS pmo_artifact_links (
 reference_id VARCHAR(64) PRIMARY KEY,
 project_id VARCHAR(255) NOT NULL,
 wbs_id VARCHAR(255) NOT NULL,
 kind VARCHAR(32) NOT NULL,
 source VARCHAR(64) NOT NULL,
 external_id VARCHAR(255) NOT NULL,
 url TEXT,
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_pmo_artifact_project_wbs
 ON pmo_artifact_links(project_id,wbs_id);
"""

def _init(conn):
    for stmt in SCHEMA.strip().split(";"):
        if stmt.strip(): conn.execute(text(stmt))

def register(project,wbs,kind,source,external_id,url=None,metadata=None):
    ref=stable_id(project,wbs,kind,source,external_id)
    if url is not None and (not isinstance(url,str) or not url.startswith("https://")):
        raise ValueError("URL must be HTTPS")
    if metadata is not None and not isinstance(metadata,dict):
        raise ValueError("metadata must be an object")
    with get_engine().begin() as conn:
        _init(conn)
        conn.execute(text("""INSERT INTO pmo_artifact_links
          (reference_id,project_id,wbs_id,kind,source,external_id,url,metadata)
          VALUES (:id,:project,:wbs,:kind,:source,:external,:url,CAST(:metadata AS JSONB))
          ON CONFLICT(reference_id) DO UPDATE
          SET url=EXCLUDED.url,metadata=EXCLUDED.metadata,updated_at=now()"""),
          {"id":ref,"project":project,"wbs":wbs,"kind":kind,"source":source,
           "external":external_id,"url":url,"metadata":json.dumps(metadata or {})})
    return {"reference_id":ref,"project_id":project,"wbs_id":wbs}

def list_links(project,wbs,limit=100):
    if not project or not wbs or not 1<=limit<=500: raise ValueError("invalid scope or limit")
    with get_engine().begin() as conn:
        _init(conn)
        rows=conn.execute(text("""SELECT reference_id,project_id,wbs_id,kind,source,
            external_id,url,metadata FROM pmo_artifact_links
            WHERE project_id=:project AND wbs_id=:wbs
            ORDER BY kind,source,external_id LIMIT :limit"""),
            {"project":project,"wbs":wbs,"limit":limit}).mappings().all()
    return [dict(row) for row in rows]
