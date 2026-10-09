from app.artifact_registry import stable_id

def test_stable():
    assert stable_id('P','W','wiki','docmost','1') == stable_id('P','W','wiki','docmost','1')
    assert stable_id('P','W','wiki','docmost','1') != stable_id('P','W','wiki','docmost','2')
