from app import project_connectors as pc
from urllib.parse import parse_qs, urlsplit
import pytest

def test_jira_pages(monkeypatch):
    seen=[]
    def fake(url, headers):
        seen.append(int(parse_qs(urlsplit(url).query)["startAt"][0]))
        return {"issues":[{"key":str(i)} for i in range(100)] if len(seen)==1 else [{"key":"last"}],"total":101}
    monkeypatch.setattr(pc,"_request_json",fake)
    items=pc.read_jira_pages("P",base_url="https://jira.example.org",email="test",token="test",max_pages=3)
    assert len(items)==101
    assert seen==[0,100]

def test_plane_pages(monkeypatch):
    seen=[]
    def fake(url,headers):
        seen.append(int(parse_qs(urlsplit(url).query)["page"][0]))
        return {"results":[{"id":str(i)} for i in range(100)] if len(seen)==1 else []}
    monkeypatch.setattr(pc,"_request_json",fake)
    assert len(pc.read_plane_pages("team","project",base_url="https://plane.example.org",token="test"))==100
    assert seen==[1,2]

def test_invalid_page_limit():
    with pytest.raises(ValueError): pc.read_jira_pages("P",max_pages=6)
    with pytest.raises(ValueError): pc.read_plane_pages("team","project",max_pages=0)
