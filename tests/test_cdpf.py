import pytest
from datetime import datetime,timezone
from app.cdpf.engine import Signal,EvaluateRequest,evaluate
from app.cdpf.adapters import normalize
NOW=datetime.now(timezone.utc)
def signal(dim,score,id):
    return Signal(source="aipmo",source_id=id,dimension=dim,severity=score,observed_at=NOW)
def test_empty():
    r=evaluate(EvaluateRequest(project_id="P",signals=[]))
    assert r["risk_score"] is None and r["level"]=="unknown"
def test_weighted():
    r=evaluate(EvaluateRequest(project_id="P",signals=[signal("expectation",80,"1"),signal("quality",20,"2")]))
    assert r["risk_score"]==53.33 and r["coverage"]==.45
def test_dedup():
    r=evaluate(EvaluateRequest(project_id="P",signals=[signal("quality",20,"1"),signal("quality",90,"1")]))
    assert r["evidence_count"]==1 and r["risk_score"]==90
def test_bad_dimension():
    with pytest.raises(ValueError): evaluate(EvaluateRequest(project_id="P",signals=[signal("bad",20,"1")]))
def test_adapter():
    r=normalize("plane",[{"id":"ISSUE-1","event_type":"reopened_issue","severity":90,"observed_at":NOW.isoformat()}])
    assert r[0].dimension=="quality"
def test_bad_severity():
    with pytest.raises(ValueError): normalize("kiwi",[{"id":"t","event_type":"failed_test","severity":120,"observed_at":NOW.isoformat()}])
def test_unknown_source():
    with pytest.raises(ValueError): normalize("bad",[])
