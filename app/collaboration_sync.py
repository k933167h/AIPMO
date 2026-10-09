"""Transactional collaboration sync with idempotent batch and checkpoint."""
import json
from sqlalchemy import text
from app.store import get_engine
from app.artifact_registry import stable_id
from app.artifact_store import _init

DDL = """CREATE TABLE IF NOT EXISTS pmo_collab_sync_state (
 project_id VARCHAR(255) NOT NULL,
 provider VARCHAR(32) NOT NULL,
 scope VARCHAR(255) NOT NULL,
 cursor_value VARCHAR(255),
 last_error TEXT,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(project_id,provider,scope)
)"""

def apply_batch(project,provider,scope,items,cursor):
    if provider not in ("zulip","nextcloud") or not project or not scope:
        raise ValueError("invalid sync scope")
    if not isinstance(items,list) or len(items)>500: raise ValueError("invalid batch")
    if cursor is not None and (not isinstance(cursor,str) or len(cursor)>255):
        raise ValueError("invalid cursor")
    with get_engine().begin() as conn:
        _init(conn)
        conn.execute(text(DDL))
        conn.execute(text("""INSERT INTO pmo_collab_sync_state(project_id,provider,scope)
            VALUES (:p,:v,:s) ON CONFLICT DO NOTHING"""),{"p":project,"v":provider,"s":scope})
        conn.execute(text("""SELECT cursor_value FROM pmo_collab_sync_state
            WHERE project_id=:p AND provider=:v AND scope=:s FOR UPDATE"""),
            {"p":project,"v":provider,"s":scope})
        for item in items:
            ref=stable_id(project,item["wbs_id"],item["kind"],provider,item["external_id"])
            conn.execute(text("""INSERT INTO pmo_artifact_links
                (reference_id,project_id,wbs_id,kind,source,external_id,url,metadata)
                VALUES (:id,:p,:w,:k,:v,:e,NULL,CAST(:m AS JSONB))
                ON CONFLICT(reference_id) DO UPDATE
                SET metadata=EXCLUDED.metadata,updated_at=now()"""),
                {"id":ref,"p":project,"w":item["wbs_id"],"k":item["kind"],
                 "v":provider,"e":item["external_id"],
                 "m":json.dumps(item.get("metadata",{}))})
        conn.execute(text("""UPDATE pmo_collab_sync_state SET cursor_value=:c,
            last_error=NULL,updated_at=now()
            WHERE project_id=:p AND provider=:v AND scope=:s"""),
            {"c":cursor,"p":project,"v":provider,"s":scope})
    return {"registered":len(items),"cursor":cursor}

def read_cursor(project,provider,scope):
    with get_engine().begin() as conn:
        conn.execute(text(DDL))
        row=conn.execute(text("""SELECT cursor_value FROM pmo_collab_sync_state
            WHERE project_id=:p AND provider=:v AND scope=:s"""),
            {"p":project,"v":provider,"s":scope}).first()
    return row[0] if row else None
