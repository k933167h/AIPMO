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
