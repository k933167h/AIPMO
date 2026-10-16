"""Native API response translators. Source requests remain configured in polling.py."""
from datetime import datetime,timezone
from .engine import Signal

def _time(value):
    if not value: raise ValueError("event timestamp missing")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("timezone required")
    return dt

def _signal(source,id,dimension,severity,observed):
    return Signal(source=source,source_id=str(id),dimension=dimension,severity=max(0,min(100,float(severity))),observed_at=_time(observed))

def plane(issues):
    """Plane work items: state-group and target-date fields must be validated per deployment."""
    out=[]
    for i in issues:
        if not i.get("id"): continue
        observed=i.get("updated_at") or i.get("created_at")
        if not observed: continue
        if i.get("target_date"):
            target=datetime.fromisoformat(i["target_date"])
            if target.date()<datetime.now(timezone.utc).date() and i.get("state__group") not in ("completed","cancelled"):
                out.append(_signal("plane",i["id"],"schedule",80,observed))
    return out

def kiwi(executions):
    """Kiwi execution result values are instance-specific; configure failed statuses."""
    out=[]
    for e in executions:
        status=str(e.get("status",e.get("status_name",""))).lower()
        if status not in ("failed","fail","blocked"): continue
        if e.get("id") and (e.get("stop_date") or e.get("start_date")):
            out.append(_signal("kiwi",e["id"],"quality",90 if status!="blocked" else 65,e.get("stop_date") or e.get("start_date")))
    return out

def langfuse(observations):
    """Langfuse score records: low scores in [0,1] signal quality risk."""
    out=[]
    for s in observations:
        if not s.get("id") or s.get("value") is None: continue
        name=str(s.get("name","")).lower()
        if name not in ("groundedness","factuality","answer_relevance"): continue
        score=float(s["value"])
        if not 0<=score<=1: raise ValueError("score must be in [0,1]")
        observed=s.get("timestamp") or s.get("createdAt")
        if observed: out.append(_signal("langfuse",s["id"],"ai_trust",(1-score)*100,observed))
    return out

TRANSLATORS={"plane":plane,"kiwi":kiwi,"langfuse":langfuse}
