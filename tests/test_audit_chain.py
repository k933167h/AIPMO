from app.audit_chain import GENESIS,event_hash,verify_events

def test_chain_verification():
    baseline_id="B1"
    first={"action":"PROPOSED","actor":"system","occurred_at":"2026-10-09T00:00:00+00:00","prev_hash":GENESIS}
    first["event_hash"]=event_hash(baseline_id,first["action"],first["actor"],first["occurred_at"],GENESIS)
    second={"action":"APPROVED","actor":"alice","occurred_at":"2026-10-09T00:01:00+00:00","prev_hash":first["event_hash"]}
    second["event_hash"]=event_hash(baseline_id,second["action"],second["actor"],second["occurred_at"],second["prev_hash"])
    assert verify_events(baseline_id,[first,second])["valid"] is True
    second["actor"]="mallory"
    assert verify_events(baseline_id,[first,second])["valid"] is False

def test_broken_link():
    event={"action":"PROPOSED","actor":"system","occurred_at":"2026-10-09T00:00:00+00:00",
           "prev_hash":"bad","event_hash":"bad"}
    assert verify_events("B1",[event])["reason"]=="previous hash mismatch"
