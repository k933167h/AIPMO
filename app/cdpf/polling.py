"""Configurable external API polling, with strict host and field mapping."""
import os
import ipaddress
import socket
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel, Field
from .adapters import normalize
from .persistence import persist

class PollSource(BaseModel):
    name:str
    url:str
    token_env:str
    project_id:str=Field(min_length=1)
    timeout_seconds:float=Field(default=10,gt=0,le=60)
    events_key:str="results"

def validate_url(url:str):
    parsed=urlparse(url)
    if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("HTTPS URL without credentials or fragment required")
    allowed={h.strip().lower() for h in os.getenv("CDPF_ALLOWED_HOSTS","").split(",") if h.strip()}
    if parsed.hostname.lower() not in allowed:
        raise ValueError("host not in CDPF_ALLOWED_HOSTS")
    # DNS rebinding protection requires network egress restrictions in deployment.
    return url

def fetch_records(source:PollSource,client:httpx.Client):
    validate_url(source.url)
    token=os.getenv(source.token_env)
    if not token: raise RuntimeError("missing source token environment variable")
    response=client.get(source.url,headers={"Authorization":f"Bearer {token}"},timeout=source.timeout_seconds,follow_redirects=False)
    response.raise_for_status()
    data=response.json()
    if isinstance(data,list): records=data
    elif isinstance(data,dict): records=data.get(source.events_key)
    else: records=None
    if not isinstance(records,list): raise ValueError("expected JSON list of records")
    if len(records)>10000: raise ValueError("too many records")
    return records

def poll_once(source:PollSource,client:httpx.Client):
    if source.name not in {"aipmo","plane","kiwi","langfuse"}:
        raise ValueError("unsupported source")
    records=fetch_records(source,client)
    signals=normalize(source.name,records)
    saved=persist(source.project_id,signals)
    return {"source":source.name,"fetched":len(records),"normalized":len(signals),**saved}
