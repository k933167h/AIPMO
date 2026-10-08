import pytest
from app.schedule import critical_path

def test_parallel_paths():
    result=critical_path([{"id":"A","duration":3},{"id":"B","duration":5},{"id":"C","duration":2,"predecessors":["A"]},{"id":"D","duration":1,"predecessors":["B"]}])
    assert result["project_duration_days"]==6
    assert result["critical_task_ids"]==["B","D"]
    assert next(t for t in result["tasks"] if t["id"]=="A")["total_float"]==1

def test_cycle():
    with pytest.raises(ValueError,match="cyclic"):
        critical_path([{"id":"A","duration":1,"predecessors":["B"]},{"id":"B","duration":1,"predecessors":["A"]}])

def test_missing_predecessor():
    with pytest.raises(ValueError,match="missing"):
        critical_path([{"id":"A","duration":1,"predecessors":["missing"]}])

def test_empty():
    assert critical_path([])["project_duration_days"]==0
