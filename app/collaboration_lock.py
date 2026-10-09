"""Database advisory lock for project/provider/scope workers."""
import hashlib
from sqlalchemy import text
from app.store import get_engine

def lock_key(project,provider,scope):
    data="|".join((project,provider,scope)).encode()
    return int.from_bytes(hashlib.sha256(data).digest()[:8],"big",signed=True)

def run_exclusive(project,provider,scope,operation):
    engine=get_engine()
    with engine.connect() as conn:
        key=lock_key(project,provider,scope)
        acquired=conn.execute(text("SELECT pg_try_advisory_lock(:key)"),{"key":key}).scalar()
        if not acquired: raise RuntimeError("sync scope already active")
        try:
            return operation()
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:key)"),{"key":key})
