"""Safe bounded chunk commits for monotonic Zulip message IDs."""
from app.collaboration_sync import apply_batch

def commit_message_chunks(project,scope,messages,chunk_size=250):
    if not 1<=chunk_size<=500: raise ValueError("invalid chunk size")
    ordered=sorted(messages,key=lambda m:int(m["id"]))
    ids=[int(m["id"]) for m in ordered]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate message ID")
    committed=0
    last=None
    for offset in range(0,len(ordered),chunk_size):
        batch=ordered[offset:offset+chunk_size]
        items=[]
        for message in batch:
            for wbs in message.get("wbs_ids",[]):
                items.append({"wbs_id":wbs,"kind":"message","external_id":str(message["id"])})
        if len(items)>500: raise ValueError("chunk contains too many WBS links")
        last=str(batch[-1]["id"])
        apply_batch(project,"zulip",scope,items,last)
        committed+=len(items)
    return {"registered":committed,"cursor":last}
