"""Atomic persistence of project work items and checkpoints."""
from datetime import datetime, timezone
import json
import uuid
from sqlalchemy import text
from app.store import get_engine
from app.sync_checkpoints import SCHEMA

ITEM_SCHEMA = """
CREATE TABLE IF NOT EXISTS pmo_sync_items (
 project_key VARCHAR(255) NOT NULL,
 provider VARCHAR(32) NOT NULL,
 external_id VARCHAR(255) NOT NULL,
 payload JSONB NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL,
 PRIMARY KEY(project_key,provider,external_id)
);
"""

def parse_updated(value):
    if not value: raise ValueError("missing updated timestamp")
    parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if parsed.tzinfo is None: raise ValueError("timestamp requires timezone")
    return parsed.astimezone(timezone.utc)

def prepare(provider, items):
    if provider not in ("jira","plane"): raise ValueError("invalid provider")
    prepared=[]
    for item in items:
        identifier=item.get("key") if provider=="jira" else item.get("id")
        if not identifier: raise ValueError("missing external ID")
        value=(item.get("fields") or {}).get("updated") if provider=="jira" else item.get("updated_at")
        prepared.append((str(identifier),parse_updated(value),json.dumps(item,ensure_ascii=False)))
    return prepared

def persist_items(project_key,provider,items,complete=True):
    if not project_key or not complete: raise ValueError("invalid or incomplete collection")
    prepared=prepare(provider,items)
    now=datetime.now(timezone.utc)
    watermark=max((stamp for _,stamp,_ in prepared),default=None)
    run_id=str(uuid.uuid4())
    with get_engine().begin() as conn:
        for statement in (SCHEMA+ITEM_SCHEMA).strip().split(";"):
            if statement.strip(): conn.execute(text(statement))
        for identifier,stamp,payload in prepared:
            conn.execute(text("""INSERT INTO pmo_sync_items
             (project_key,provider,external_id,payload,updated_at)
             VALUES (:project,:provider,:id,CAST(:payload AS JSONB),:updated)
             ON CONFLICT(project_key,provider,external_id)
             DO UPDATE SET payload=EXCLUDED.payload,updated_at=EXCLUDED.updated_at
             WHERE pmo_sync_items.updated_at<=EXCLUDED.updated_at"""),
             {"project":project_key,"provider":provider,"id":identifier,"payload":payload,"updated":stamp})
        conn.execute(text("""INSERT INTO pmo_sync_runs
         (id,project_key,provider,status,observed_count,started_at,completed_at,error_code)
         VALUES (:id,:project,:provider,'SUCCESS',:count,:at,:at,NULL)"""),
         {"id":run_id,"project":project_key,"provider":provider,"count":len(prepared),"at":now})
        if watermark:
            conn.execute(text("""INSERT INTO pmo_sync_checkpoints
             (project_key,provider,watermark,updated_at)
             VALUES (:project,:provider,:watermark,:at)
             ON CONFLICT(project_key,provider)
             DO UPDATE SET watermark=GREATEST(pmo_sync_checkpoints.watermark,EXCLUDED.watermark),
                           updated_at=EXCLUDED.updated_at"""),
             {"project":project_key,"provider":provider,"watermark":watermark,"at":now})
    return {"run_id":run_id,"status":"SUCCESS","stored_count":len(prepared),
            "watermark":watermark.isoformat() if watermark else None}
