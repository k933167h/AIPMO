"""Persist successful collection cursors transactionally after evidence writes."""
from datetime import datetime,timezone
from sqlalchemy import text
from app.store import get_engine
from .persistence import DDL,UPSERT
from .engine import Signal
CURSOR_DDL="""CREATE TABLE IF NOT EXISTS cdpf_cursors (
 project_id VARCHAR(255) NOT NULL, source VARCHAR(80) NOT NULL,
 cursor_value VARCHAR(512) NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
 PRIMARY KEY(project_id,source));"""
def checkpoint(project_id:str,source:str,signals:list[Signal],cursor:str):
    if not project_id or not source or not cursor: raise ValueError("project, source and cursor required")
    now=datetime.now(timezone.utc)
    with get_engine().begin() as conn:
        for statement in DDL.strip().split(";"):
            if statement.strip(): conn.execute(text(statement))
        conn.execute(text(CURSOR_DDL))
        for s in signals:
            conn.execute(text(UPSERT),dict(project_id=project_id,**s.model_dump(),received_at=now))
        conn.execute(text("""INSERT INTO cdpf_cursors(project_id,source,cursor_value,updated_at)
        VALUES (:project,:source,:cursor,:now)
        ON CONFLICT(project_id,source) DO UPDATE SET cursor_value=EXCLUDED.cursor_value,updated_at=EXCLUDED.updated_at"""),
        {"project":project_id,"source":source,"cursor":cursor,"now":now})
    return {"project_id":project_id,"source":source,"saved":len(signals),"cursor":cursor}
def get_cursor(project_id:str,source:str):
    with get_engine().begin() as conn:
        conn.execute(text(CURSOR_DDL))
        return conn.execute(text("SELECT cursor_value FROM cdpf_cursors WHERE project_id=:p AND source=:s"),
        {"p":project_id,"s":source}).scalar_one_or_none()
