import pytest
from app.cdpf.native import plane,kiwi,langfuse
def test_plane_overdue():
    r=plane([{"id":"i1","target_date":"2020-01-01","updated_at":"2026-10-16T10:00:00Z","state__group":"started"}])
    assert r[0].dimension=="schedule" and r[0].severity==80
def test_plane_complete():
    assert plane([{"id":"i1","target_date":"2020-01-01","updated_at":"2026-10-16T10:00:00Z","state__group":"completed"}])==[]
def test_kiwi_failed():
    assert kiwi([{"id":2,"status_name":"FAILED","stop_date":"2026-10-16T10:00:00Z"}])[0].severity==90
def test_langfuse_low_score():
    assert langfuse([{"id":"s","name":"groundedness","value":0.2,"timestamp":"2026-10-16T10:00:00Z"}])[0].severity==80
def test_langfuse_invalid():
    with pytest.raises(ValueError): langfuse([{"id":"s","name":"groundedness","value":1.2,"timestamp":"2026-10-16T10:00:00Z"}])
