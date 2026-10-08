import pytest
from app.schedule import critical_path

def by_id(result,task_id):
    return next(t for t in result["tasks"] if t["id"]==task_id)

@pytest.mark.parametrize("kind,expected",[
    ("FS",7),("SS",3),("FF",4),("SF",3)])
def test_dependency_types(kind,expected):
    result=critical_path([{"id":"A","duration":4},{"id":"B","duration":3,
       "predecessors":[{"id":"A","type":kind,"lag":0}]}])
    assert by_id(result,"B")["early_start"]==expected-3

def test_positive_lag():
    result=critical_path([{"id":"A","duration":4},{"id":"B","duration":3,
       "predecessors":[{"id":"A","type":"FS","lag":2}]}])
    assert by_id(result,"B")["early_start"]==6

def test_negative_lead():
    result=critical_path([{"id":"A","duration":4},{"id":"B","duration":3,
       "predecessors":[{"id":"A","type":"FS","lag":-2}]}])
    assert by_id(result,"B")["early_start"]==2

def test_multiple_constraints():
    result=critical_path([{"id":"A","duration":4},{"id":"B","duration":2},
       {"id":"C","duration":3,"predecessors":[{"id":"A","type":"FS"},{"id":"B","type":"SS","lag":5}]}])
    assert by_id(result,"C")["early_start"]==5

def test_invalid_type():
    with pytest.raises(ValueError,match="invalid dependency"):
        critical_path([{"id":"A","duration":1},{"id":"B","duration":1,
            "predecessors":[{"id":"A","type":"XY"}]}])

def test_cycle():
    with pytest.raises(ValueError,match="cyclic"):
        critical_path([{"id":"A","duration":1,"predecessors":["B"]},
                       {"id":"B","duration":1,"predecessors":["A"]}])
