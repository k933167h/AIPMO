import pytest
from app.engine import progress, evm

def test_progress():
    assert progress([{"weight":2,"completion":0.5},{"weight":2,"completion":1}]) == 75

def test_empty():
    assert progress([]) is None

def test_invalid():
    with pytest.raises(ValueError):
        progress([{"weight":1,"completion":2}])

def test_evm():
    result=evm(100,80,80,200)
    assert result["spi"]==0.8 and result["cpi"]==1.0
