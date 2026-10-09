import pytest
from app.collaboration_retry import retry
from app import collaboration_delta_worker as worker

def test_retry_transient_failure():
    attempts=[]
    def action():
        attempts.append(1)
        if len(attempts)<3: raise TimeoutError()
        return "ok"
    assert retry(action,attempts=3,sleep=lambda t:None)=="ok"
    assert len(attempts)==3

def test_zulip_delta_checkpoint(monkeypatch):
    captured=[]
    monkeypatch.setattr(worker,"check_project_access",lambda p:True)
    monkeypatch.setattr(worker,"read_cursor",lambda *args:"10")
    monkeypatch.setattr(worker,"fetch_zulip_since",lambda *args,**kwargs:[
        {"id":10,"subject":"WBS-1"},{"id":11,"subject":"WBS-2"}])
    monkeypatch.setattr(worker,"apply_batch",lambda p,v,s,items,cursor:
        captured.append((items,cursor)) or {"registered":len(items),"cursor":cursor})
    monkeypatch.setattr(worker,"record",lambda *args,**kwargs:None)
    result=worker.run_zulip_delta("P",7)
    assert result["registered"]==1
    assert captured[0][1]=="11"
