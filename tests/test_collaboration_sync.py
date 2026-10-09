import uuid
import pytest
from app.collaboration_sync import apply_batch,read_cursor
from app.artifact_store import list_links

def test_atomic_batch_and_checkpoint():
    project="sync-"+uuid.uuid4().hex[:12]
    item={"wbs_id":"WBS-12","kind":"message","external_id":"99"}
    assert apply_batch(project,"zulip","stream-1",[item],"99")["registered"]==1
    assert read_cursor(project,"zulip","stream-1")=="99"
    apply_batch(project,"zulip","stream-1",[item],"99")
    assert len(list_links(project,"WBS-12"))==1
    with pytest.raises(ValueError):
        apply_batch(project,"zulip","stream-1",[item,{"wbs_id":"WBS-12","kind":"invalid","external_id":"100"}],"100")
    assert read_cursor(project,"zulip","stream-1")=="99"
    assert len(list_links(project,"WBS-12"))==1

def test_reject_oversized_batch():
    with pytest.raises(ValueError):
        apply_batch("P","zulip","stream-1",[{}]*501,"1")
