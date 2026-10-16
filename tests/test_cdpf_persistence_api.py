import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.cdpf.engine import Signal

client=TestClient(app)
HEADERS={"X-API-Key":"test-key"}
def test_auth(monkeypatch):
    monkeypatch.setenv("PMO_API_KEY","test-key")
    assert client.get("/api/v1/cdpf/projects/P1/risk").status_code==401
def test_ingest_calls_persistence(monkeypatch):
    monkeypatch.setenv("PMO_API_KEY","test-key")
    calls=[]
    def fake_persist(project,signals):
        calls.append((project,signals))
        return {"project_id":project,"processed":len(signals)}
    monkeypatch.setattr("app.cdpf.persistence.persist",fake_persist)
    body={"project_id":"P1","source":"plane","records":[{"id":"I1","event_type":"reopened_issue","severity":90,"observed_at":"2026-10-16T09:00:00Z"}]}
    r=client.post("/api/v1/cdpf/ingest",headers=HEADERS,json=body)
    assert r.status_code==200 and r.json()["processed"]==1
    assert calls[0][1][0].dimension=="quality"
def test_project_risk(monkeypatch):
    monkeypatch.setenv("PMO_API_KEY","test-key")
    monkeypatch.setattr("app.cdpf.persistence.project_risk",lambda project:{"project_id":project,"level":"watch"})
    r=client.get("/api/v1/cdpf/projects/P1/risk",headers=HEADERS)
    assert r.status_code==200 and r.json()["level"]=="watch"
