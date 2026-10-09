import pytest
from app import zulip_pagination as paging
from app.collaboration_lock import lock_key

def test_paging_collects_multiple_pages(monkeypatch):
    monkeypatch.setenv("PMO_ZULIP_URL","https://zulip.internal")
    monkeypatch.setenv("PMO_ZULIP_EMAIL","bot@internal")
    monkeypatch.setenv("PMO_ZULIP_API_KEY","test")
    pages=iter([
        {"result":"success","found_newest":False,"messages":[{"id":11,"stream_id":7}]},
        {"result":"success","found_newest":True,"messages":[{"id":12,"stream_id":7}]}])
    monkeypatch.setattr(paging,"_json_get",lambda *args:next(pages))
    assert [m["id"] for m in paging.fetch_zulip_since(7,"10")]==[11,12]

def test_page_budget_fails_closed(monkeypatch):
    monkeypatch.setenv("PMO_ZULIP_URL","https://zulip.internal")
    monkeypatch.setenv("PMO_ZULIP_EMAIL","bot@internal")
    monkeypatch.setenv("PMO_ZULIP_API_KEY","test")
    monkeypatch.setattr(paging,"_json_get",lambda *args:{"result":"success","found_newest":False,"messages":[{"id":11,"stream_id":7}]})
    with pytest.raises(RuntimeError):
        paging.fetch_zulip_since(7,"10",max_pages=1)

def test_scope_lock_key():
    assert lock_key("P","zulip","stream-7")==lock_key("P","zulip","stream-7")
    assert lock_key("P","zulip","stream-7")!=lock_key("P","zulip","stream-8")
