from datetime import datetime,timezone
import pytest
from app.sync_checkpoints import record_sync,read_checkpoint

def test_success_checkpoint_roundtrip(monkeypatch):
    from app import sync_checkpoints as sc
    from app.store import get_engine
    engine=get_engine()
    monkeypatch.setattr(sc,"get_engine",lambda:engine)
    project="checkpoint-test-success"
    stamp=datetime(2026,10,9,tzinfo=timezone.utc)
    result=record_sync(project,"jira",stamp,2)
    assert result["status"]=="SUCCESS"
    assert read_checkpoint(project,"jira").startswith("2026-10-09")

def test_failed_run_does_not_advance(monkeypatch):
    from app import sync_checkpoints as sc
    from app.store import get_engine
    engine=get_engine()
    monkeypatch.setattr(sc,"get_engine",lambda:engine)
    project="checkpoint-test-failure"
    record_sync(project,"plane",datetime(2026,10,10,tzinfo=timezone.utc),0,success=False,error_code="UPSTREAM")
    assert read_checkpoint(project,"plane") is None

def test_invalid_scope():
    with pytest.raises(ValueError):
        record_sync("P","unknown",None,0)
