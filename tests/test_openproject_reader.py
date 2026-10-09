import httpx
import pytest
from app.openproject_reader import read_work_packages


def test_openproject_pagination(monkeypatch):
    monkeypatch.setenv("OPENPROJECT_URL", "https://op.example.org")
    monkeypatch.setenv("OPENPROJECT_API_TOKEN", "test-secret")
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.path == "/api/v3/projects/7/work_packages"
        assert request.headers["authorization"].startswith("Basic ")
        page = int(request.url.params["offset"])
        elements = [{"id": page}] if page <= 2 else []
        return httpx.Response(200, json={"total": 2, "_embedded": {"elements": elements}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = read_work_packages(7, max_pages=3, page_size=1, client=client)
    assert result["count"] == 2
    assert len(calls) == 2


def test_reject_http_origin(monkeypatch):
    monkeypatch.setenv("OPENPROJECT_URL", "http://op.example.org")
    monkeypatch.setenv("OPENPROJECT_API_TOKEN", "test-secret")
    with pytest.raises(ValueError):
        read_work_packages(7)


def test_reject_invalid_project(monkeypatch):
    with pytest.raises(ValueError):
        read_work_packages(0)


def test_reject_malformed_response(monkeypatch):
    monkeypatch.setenv("OPENPROJECT_URL", "https://op.example.org")
    monkeypatch.setenv("OPENPROJECT_API_TOKEN", "test-secret")
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={}))) as client:
        with pytest.raises(ValueError):
            read_work_packages(7, client=client)
