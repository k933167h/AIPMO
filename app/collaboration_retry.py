"""Bounded retry policy and auditable collaboration sync runs."""
import random
import time
from sqlalchemy import text
from app.store import get_engine

DDL = """CREATE TABLE IF NOT EXISTS pmo_collab_sync_audit (
 id BIGSERIAL PRIMARY KEY,
 project_id VARCHAR(255) NOT NULL,
 provider VARCHAR(32) NOT NULL,
 scope VARCHAR(255) NOT NULL,
 status VARCHAR(24) NOT NULL,
 item_count INTEGER NOT NULL DEFAULT 0,
 error_code VARCHAR(64),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)"""

def record(project,provider,scope,status,count=0,error_code=None):
    with get_engine().begin() as conn:
        conn.execute(text(DDL))
        conn.execute(text("""INSERT INTO pmo_collab_sync_audit
            (project_id,provider,scope,status,item_count,error_code)
            VALUES (:p,:v,:s,:status,:count,:error)"""),
            {"p":project,"v":provider,"s":scope,"status":status,
             "count":count,"error":error_code})

def retry(operation,attempts=3,base_delay=0.2,sleep=time.sleep):
    if not 1<=attempts<=5: raise ValueError("invalid retry limit")
    for attempt in range(attempts):
        try:
            return operation()
        except (TimeoutError,ConnectionError):
            if attempt+1==attempts: raise
            sleep(min(5,base_delay*(2**attempt))*(0.5+random.random()/2))
