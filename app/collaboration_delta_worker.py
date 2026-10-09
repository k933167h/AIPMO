"""On-demand delta worker for Zulip with durable checkpoints."""
from app.collaboration_sync import apply_batch,read_cursor
from app.collaboration_retry import record,retry
from app.collaboration_discovery import zulip_recent_messages
from app.collaboration_mapping import detect_wbs
from app.sync_policy import check_project_access

def run_zulip_delta(project,stream_id,limit=100):
    check_project_access(project)
    if not isinstance(stream_id,int) or stream_id<=0 or not 1<=limit<=100:
        raise ValueError("invalid stream or limit")
    scope=f"stream-{stream_id}"
    previous=read_cursor(project,"zulip",scope)
    try:
        messages=retry(lambda:zulip_recent_messages(stream_id,limit))
        ordered=sorted(messages,key=lambda m:int(m["id"]))
        newer=[m for m in ordered if previous is None or int(m["id"])>int(previous)]
        items=[]
        for message in newer:
            for wbs in detect_wbs(str(message.get("subject") or "")):
                items.append({"wbs_id":wbs,"kind":"message","external_id":str(message["id"])})
        cursor=str(newer[-1]["id"]) if newer else previous
        result=apply_batch(project,"zulip",scope,items,cursor)
        record(project,"zulip",scope,"success",result["registered"])
        return result
    except Exception:
        record(project,"zulip",scope,"failed",error_code="SYNC_FAILURE")
        raise
