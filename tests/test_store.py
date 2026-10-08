import pytest
from app.ganttax import normalize_project
from app.store import stage_import

def test_normalized_state_keeps_extensions():
    state={"project":{"code":"X"},"tasks":[],"holidays":["2026-10-09"]}
    assert normalize_project(state)["extensions"]["holidays"] == ["2026-10-09"]

def test_no_db_is_explicit(monkeypatch):
    monkeypatch.delenv("DATABASE_URL",raising=False)
    with pytest.raises(RuntimeError,match="DATABASE_URL"):
        stage_import({"project":{},"tasks":[]})
