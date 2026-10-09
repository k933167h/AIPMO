"""On-demand delta worker for Zulip with durable checkpoints."""
from app.collaboration_sync import apply_batch,read_cursor
from app.collaboration_retry import record,retry
from app.zulip_pagination import fetch_zulip_since
from app.collaboration_mapping import detect_wbs
from app.collaboration_stream import commit_message_chunks
from app.sync_policy import check_project_access

def run_zulip_delta(project,stream_id,limit=100):
    check_project_access(project)
    if not isinstance(stream_id,int) or stream_id<=0 or not 1<=limit<=100:
        raise ValueError("invalid stream or limit")
    scope=f"stream-{stream_id}"
    previous=read_cursor(project,"zulip",scope)
    try:
        messages=retry(lambda:fetch_zulip_since(stream_id,previous,page_size=limit))
        ordered=sorted(messages,key=lambda m:int(m["id"]))
        newer=[m for m in ordered if previous is None or int(m["id"])>int(previous)]
        chunk_messages=[{"id":m["id"],"wbs_ids":detect_wbs(str(m.get("subject") or ""))} for m in newer]
        result=commit_message_chunks(project,scope,chunk_messages) if chunk_messages else {"registered":0,"cursor":previous}
        record(project,"zulip",scope,"success",result["registered"])
        return result
    except Exception:
        record(project,"zulip",scope,"failed",error_code="SYNC_FAILURE")
        raise
