import pytest
from app.github_reader import map_wbs_links,fetch_github_snapshot

def test_wbs_reference_from_title():
    snapshot={"issues":[{"external_id":"github:issue:1","type":"issue","title":"WBS-APGW-01 implement gateway","url":"https://example.com"}],
              "pull_requests":[{"external_id":"github:pr:2","type":"pull_request","title":"WBS:DLH-02 pipeline","url":None}]}
    links=map_wbs_links(snapshot)
    assert [x["wbs_id"] for x in links]==["APGW-01","DLH-02"]

def test_invalid_repository_rejected():
    with pytest.raises(ValueError,match="invalid repository"):
        fetch_github_snapshot("https://evil.example/repo",token="dummy")

def test_token_required(monkeypatch):
    monkeypatch.delenv("PMO_GITHUB_READ_TOKEN",raising=False)
    with pytest.raises(ValueError,match="TOKEN"):
        fetch_github_snapshot("example/repo")
