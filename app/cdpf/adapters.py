from .engine import Signal
MAPPING={
"aipmo":{"late_milestone":"schedule","unanswered_request":"communication","unapproved_change":"expectation"},
"plane":{"reopened_issue":"quality","overdue_issue":"schedule","blocked_issue":"communication"},
"kiwi":{"failed_test":"quality","repeated_failure":"quality"},
"langfuse":{"hallucination":"ai_trust","low_groundedness":"ai_trust","poor_user_feedback":"adoption"}}
def normalize(source,records):
    if source not in MAPPING: raise ValueError("unsupported source")
    output=[]
    for r in records:
        dimension=MAPPING[source].get(r.get("event_type"))
        if dimension is None: continue
        if not r.get("id") or not r.get("observed_at"): raise ValueError("id and observed_at required")
        output.append(Signal(source=source,source_id=str(r["id"]),dimension=dimension,severity=float(r["severity"]),observed_at=r["observed_at"]))
    return output
