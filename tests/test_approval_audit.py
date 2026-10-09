import os
import pytest
from fastapi import HTTPException
from app.main import BaselineApproval,approve_staged_baseline
from app.approvals import propose_baseline,approve_baseline,audit_events

def test_sme_credential_required(monkeypatch):
    monkeypatch.setenv("PMO_API_KEY","test-api")
    monkeypatch.setenv("PMO_SME_APPROVAL_KEY","test-sme")
    with pytest.raises(HTTPException) as err:
        approve_staged_baseline("none",BaselineApproval(reviewer="reviewer"),"test-api","wrong")
    assert err.value.status_code==403

@pytest.mark.integration
def test_approval_audit_recorded():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    proposed=propose_baseline("AUDIT-TEST",{"tasks":[]})
    approved=approve_baseline(proposed["baseline_id"],"reviewer")
    assert approved["approval_status"]=="APPROVED"
    events=audit_events(proposed["baseline_id"])
    assert [e["action"] for e in events]==["PROPOSED","APPROVED"]
    assert events[-1]["actor"]=="reviewer"
