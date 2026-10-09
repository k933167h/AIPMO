import pytest
from app import project_connectors as pc

def test_https_validation():
    assert pc._base_url("https://jira.example.com/") == "https://jira.example.com"
    for url in ("http://example.com", "https://u:p@example.com", "https://example.com?x=1"):
        with pytest.raises(ValueError): pc._base_url(url)

def test_jira_mock(monkeypatch):
    monkeypatch.setattr(pc, "_request_json", lambda url, headers: {"issues": [{"key": "P-1", "fields": {"summary": "WBS-ABC"}}]})
    issues = pc.read_jira("P", base_url="https://jira.example.com", email="a@example.com", token="fake")
    assert issues[0]["key"] == "P-1"

def test_plane_mock(monkeypatch):
    monkeypatch.setattr(pc, "_request_json", lambda url, headers: {"results": [{"id": "1", "name": "WBS-ABC"}]})
    issues = pc.read_plane("workspace", "project", base_url="https://plane.example.com", token="fake")
    assert issues[0]["id"] == "1"

def test_reconciliation():
    data = pc.reconcile_external_work(
        [{"key":"P-1","fields":{"summary":"WBS-ABC"}}],
        [{"id":"1","name":"WBS-ABC"}])
    assert data["work_items"][0]["source_count"] == 2
