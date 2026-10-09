import json
import os
import pytest
from fastapi import HTTPException
from app.identity import resolve_identity
from app.approvals import propose_baseline,reject_baseline,audit_events,load_approved_baseline

def test_sme_identity(monkeypatch):
    monkeypatch.setenv("PMO_IDENTITIES_JSON",json.dumps({"secret":{"user_id":"alice","roles":["SME"]}}))
    assert resolve_identity("secret","SME")=="alice"
    with pytest.raises(HTTPException) as err: resolve_identity("wrong","SME")
    assert err.value.status_code==403

def test_non_sme_rejected(monkeypatch):
    monkeypatch.setenv("PMO_IDENTITIES_JSON",json.dumps({"secret":{"user_id":"bob","roles":["VIEWER"]}}))
    with pytest.raises(HTTPException) as err: resolve_identity("secret","SME")
    assert err.value.status_code==403

@pytest.mark.integration
def test_rejection_audit():
    if not os.environ.get("DATABASE_URL"): pytest.skip("DATABASE_URL not configured")
    baseline=propose_baseline("REJECT-TEST",{"tasks":[]})
    rejected=reject_baseline(baseline["baseline_id"],"alice","missing evidence")
    assert rejected["approval_status"]=="REJECTED"
    assert load_approved_baseline(baseline["baseline_id"]) is None
    assert reject_baseline(baseline["baseline_id"],"alice","repeat") is None
    assert [e["action"] for e in audit_events(baseline["baseline_id"])]==["PROPOSED","REJECTED"]
