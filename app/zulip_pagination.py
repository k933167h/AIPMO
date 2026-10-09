"""Bounded, fail-closed Zulip historical paging."""
import json
import os
from urllib.parse import quote
from app.collaboration import _base,_basic,_json_get

def fetch_zulip_since(stream_id,cursor=None,page_size=100,max_pages=20):
    if not isinstance(stream_id,int) or stream_id<=0 or not 1<=page_size<=100 or not 1<=max_pages<=50:
        raise ValueError("invalid pagination parameters")
    prior=int(cursor) if cursor is not None else 0
    base=_base(os.getenv("PMO_ZULIP_URL"))
    headers={"Authorization":_basic(os.getenv("PMO_ZULIP_EMAIL"),os.getenv("PMO_ZULIP_API_KEY"))}
    anchor=prior
    collected={}
    for page in range(max_pages):
        narrow=quote(json.dumps([{"operator":"stream","operand":stream_id}]),safe="")
        path=f"/api/v1/messages?anchor={anchor}&num_before=0&num_after={page_size}&narrow={narrow}"
        response=_json_get(base,path,headers)
        if response.get("result")!="success" or not isinstance(response.get("messages"),list):
            raise ValueError("invalid Zulip response")
        messages=response["messages"]
        for m in messages:
            ident=int(m["id"])
            if ident>prior and m.get("stream_id")==stream_id: collected[ident]=m
        if response.get("found_newest") is True:
            return [collected[i] for i in sorted(collected)]
        if not messages:
            raise RuntimeError("Zulip paging made no progress")
        newest=max(int(m["id"]) for m in messages)
        if newest<=anchor: raise RuntimeError("Zulip paging cursor stalled")
        anchor=newest
    raise RuntimeError("Zulip page budget exhausted; checkpoint unchanged")
