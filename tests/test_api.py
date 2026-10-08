import pytest
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_health():
    assert client.get("/health").json()=={"status":"ok"}

def test_unauthorized(monkeypatch):
    monkeypatch.setenv("PMO_API_KEY","test-secret")
    assert client.post("/api/v1/ganttax/imports",json={"project":{},"tasks":[]}).status_code==401

def test_invalid_project(monkeypatch):
    monkeypatch.setenv("PMO_API_KEY","test-secret")
    r=client.post("/api/v1/ganttax/imports",headers={"X-API-Key":"test-secret"},json={"project":{},"tasks":[{"id":"a","progress":110}]})
    assert r.status_code==422

def test_import_export_roundtrip(monkeypatch):
    monkeypatch.setenv("PMO_API_KEY","test-secret")
    source={"project":{"code":"P-1","name":"프로젝트"},"tasks":[{"id":"t1","name":"작업","progress":20}],"holidays":[]}
    db={}
    def fake_stage(data):
        db["state"]=data
        return {"import_id":"fixture-1","status":"STAGED","task_count":len(data["tasks"])}
    def fake_export(import_id):
        return db.get("state") if import_id=="fixture-1" else None
    monkeypatch.setattr("app.store.stage_import",fake_stage)
    monkeypatch.setattr("app.store.export_import",fake_export)
    r=client.post("/api/v1/ganttax/imports",headers={"X-API-Key":"test-secret"},json=source)
    assert r.status_code==201 and r.json()["status"]=="STAGED"
    out=client.get("/api/v1/ganttax/imports/fixture-1/export",headers={"X-API-Key":"test-secret"})
    assert out.status_code==200 and out.json()==source
    assert client.get("/api/v1/ganttax/imports/missing/export",headers={"X-API-Key":"test-secret"}).status_code==404
