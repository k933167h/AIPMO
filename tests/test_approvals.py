import os
import pytest
from app.approvals import propose_baseline,approve_baseline,load_approved_baseline

def test_invalid_baseline():
    with pytest.raises(ValueError,match="required"):
        propose_baseline("P1",{"tasks":"not-list"})

def test_reviewer_required():
    with pytest.raises(ValueError,match="reviewer"):
        approve_baseline("not-an-id","")

@pytest.mark.integration
def test_persisted_approval_lifecycle():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    baseline={"tasks":[{"id":"A","start_date":"2026-10-09","finish_date":"2026-10-13"}]}
    proposed=propose_baseline("TEST-APPROVAL",baseline)
    assert proposed["approval_status"]=="STAGED"
    assert load_approved_baseline(proposed["baseline_id"]) is None
    approved=approve_baseline(proposed["baseline_id"],"test-reviewer")
    assert approved["approval_status"]=="APPROVED"
    assert approve_baseline(proposed["baseline_id"],"test-reviewer") is None
    loaded=load_approved_baseline(proposed["baseline_id"])
    assert loaded["tasks"]==baseline["tasks"]
    assert loaded["approval_status"]=="APPROVED"
