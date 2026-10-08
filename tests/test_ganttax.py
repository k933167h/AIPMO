import pytest
from app.ganttax import normalize_project

def test_mapping():
    result=normalize_project({"project":{"name":"P","startDate":"2026-10-09"},"tasks":[{"id":"a","name":"Task","start":"2026-10-09","duration":2,"progress":50,"manDay":4}]})
    assert result["tasks"][0]["progress_pct"] == 50
    assert result["project"]["name"] == "P"

def test_duplicate_rejected():
    with pytest.raises(ValueError):
        normalize_project({"project":{},"tasks":[{"id":"a"},{"id":"a"}]})

def test_invalid_dependency():
    with pytest.raises(ValueError):
        normalize_project({"project":{},"tasks":[{"id":"a","predecessors":[{"id":"missing"}]}]})
