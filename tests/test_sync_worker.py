import pytest
from app import sync_worker
from app.sync_ingest import prepare

def test_worker_jira(monkeypatch):
    monkeypatch.setattr(sync_worker,"check_project_access",lambda key: True)
    monkeypatch.setattr(sync_worker,"read_jira_pages",lambda key,max_pages: [{"key":"P-1","fields":{"updated":"2026-10-09T00:00:00Z"}}])
    monkeypatch.setattr(sync_worker,"persist_items",lambda project,provider,records,complete: {"stored_count":len(records)})
    assert sync_worker.sync_provider("jira","P")["stored_count"]==1

def test_worker_page_cap_blocks_checkpoint(monkeypatch):
    monkeypatch.setattr(sync_worker,"check_project_access",lambda key: True)
    monkeypatch.setattr(sync_worker,"read_jira_pages",lambda key,max_pages: [{}]*100)
    monkeypatch.setattr(sync_worker,"persist_items",lambda *args,**kwargs: pytest.fail("must not persist"))
    with pytest.raises(ValueError):
        sync_worker.sync_provider("jira","P",max_pages=1)

def test_invalid_provider_record():
    with pytest.raises(ValueError):
        prepare("jira",[{"key":"P-1"}])
