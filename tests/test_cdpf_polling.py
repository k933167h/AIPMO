import pytest
import httpx
from app.cdpf.polling import PollSource,fetch_records,poll_once
def config():
    return PollSource(name="plane",url="https://plane.internal/api/events",token_env="TEST_CDPF_TOKEN",project_id="P1")
def test_allowlist(monkeypatch):
    monkeypatch.setenv("CDPF_ALLOWED_HOSTS","plane.internal")
    monkeypatch.setenv("TEST_CDPF_TOKEN","token")
    def handler(request):
        assert request.headers["Authorization"]=="Bearer token"
        return httpx.Response(200,json={"results":[{"id":"a","event_type":"reopened_issue","severity":80,"observed_at":"2026-10-16T10:00:00Z"}]})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert len(fetch_records(config(),client))==1
def test_reject_host(monkeypatch):
    monkeypatch.setenv("CDPF_ALLOWED_HOSTS","plane.internal")
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,json=[]))) as client:
        with pytest.raises(ValueError): fetch_records(config().model_copy(update={"url":"https://evil.example/data"}),client)
def test_reject_redirect(monkeypatch):
    monkeypatch.setenv("CDPF_ALLOWED_HOSTS","plane.internal")
    monkeypatch.setenv("TEST_CDPF_TOKEN","token")
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(302,headers={"location":"https://evil.example"}))) as client:
        with pytest.raises(httpx.HTTPStatusError): fetch_records(config(),client)
def test_poll_persists(monkeypatch):
    monkeypatch.setenv("CDPF_ALLOWED_HOSTS","plane.internal")
    monkeypatch.setenv("TEST_CDPF_TOKEN","token")
    monkeypatch.setattr("app.cdpf.polling.persist",lambda p,s:{"project_id":p,"processed":len(s)})
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={"results":[{"id":"i","event_type":"overdue_issue","severity":60,"observed_at":"2026-10-16T10:00:00Z"}]}))) as client:
        assert poll_once(config(),client)["processed"]==1
