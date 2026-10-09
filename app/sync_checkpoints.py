"""PostgreSQL sync checkpoints and immutable run outcomes."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
from app.store import get_engine

SCHEMA = """
CREATE TABLE IF NOT EXISTS pmo_sync_checkpoints (
  project_key VARCHAR(255) NOT NULL,
  provider VARCHAR(32) NOT NULL,
  watermark TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (project_key, provider)
);
CREATE TABLE IF NOT EXISTS pmo_sync_runs (
  id VARCHAR(36) PRIMARY KEY,
  project_key VARCHAR(255) NOT NULL,
  provider VARCHAR(32) NOT NULL,
  status VARCHAR(16) NOT NULL,
  observed_count INTEGER NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ NOT NULL,
  error_code VARCHAR(64)
);
"""

def record_sync(project_key, provider, watermark, count, success=True, error_code=None):
    if not project_key or provider not in ("jira", "plane"):
        raise ValueError("invalid sync scope")
    if not isinstance(count,int) or count<0:
        raise ValueError("invalid record count")
    if watermark is not None and (not isinstance(watermark,datetime) or watermark.tzinfo is None):
        raise ValueError("watermark must be timezone-aware")
    now=datetime.now(timezone.utc)
    run_id=str(uuid.uuid4())
    with get_engine().begin() as conn:
        for statement in SCHEMA.strip().split(";"):
            if statement.strip(): conn.execute(text(statement))
        conn.execute(text("""INSERT INTO pmo_sync_runs
          (id,project_key,provider,status,observed_count,started_at,completed_at,error_code)
          VALUES (:id,:project,:provider,:status,:count,:at,:at,:error)"""),
          {"id":run_id,"project":project_key,"provider":provider,
           "status":"SUCCESS" if success else "FAILED","count":count,
           "at":now,"error":error_code})
        if success and watermark is not None:
            conn.execute(text("""INSERT INTO pmo_sync_checkpoints
              (project_key,provider,watermark,updated_at)
              VALUES (:project,:provider,:watermark,:at)
              ON CONFLICT (project_key,provider)
              DO UPDATE SET watermark=GREATEST(pmo_sync_checkpoints.watermark,EXCLUDED.watermark),
                            updated_at=EXCLUDED.updated_at"""),
              {"project":project_key,"provider":provider,"watermark":watermark,"at":now})
    return {"run_id":run_id,"status":"SUCCESS" if success else "FAILED"}

def read_checkpoint(project_key,provider):
    if not project_key or provider not in ("jira","plane"):
        raise ValueError("invalid sync scope")
    with get_engine().begin() as conn:
        for statement in SCHEMA.strip().split(";"):
            if statement.strip(): conn.execute(text(statement))
        row=conn.execute(text("""SELECT watermark FROM pmo_sync_checkpoints
          WHERE project_key=:project AND provider=:provider"""),
          {"project":project_key,"provider":provider}).scalar_one_or_none()
    return row.isoformat() if row else None
