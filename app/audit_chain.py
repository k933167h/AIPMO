"""Canonical SHA-256 audit chain for newly recorded approval events."""
import hashlib
import json

GENESIS="0"*64

def canonical_event(baseline_id,action,actor,occurred_at,prev_hash):
    return json.dumps({"baseline_id":baseline_id,"action":action,"actor":actor,
                       "occurred_at":occurred_at,"prev_hash":prev_hash},
                      sort_keys=True,ensure_ascii=False,separators=(",",":"))

def event_hash(baseline_id,action,actor,occurred_at,prev_hash):
    payload=canonical_event(baseline_id,action,actor,occurred_at,prev_hash)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def verify_events(baseline_id,events):
    prev=GENESIS
    for index,event in enumerate(events):
        if event.get("prev_hash")!=prev:
            return {"valid":False,"first_invalid_index":index,"reason":"previous hash mismatch"}
        actual=event_hash(baseline_id,event["action"],event["actor"],
                          event["occurred_at"],event["prev_hash"])
        if actual!=event.get("event_hash"):
            return {"valid":False,"first_invalid_index":index,"reason":"event hash mismatch"}
        prev=actual
    return {"valid":True,"events_verified":len(events),"head_hash":prev}
