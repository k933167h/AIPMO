"""Deterministic WBS reference detection for collaboration metadata."""
import re
from app.artifact_registry import stable_id

WBS_TOKEN = re.compile(r"(?<![A-Za-z0-9])(?:WBS-[A-Za-z0-9_-]+|[A-Z]{2,8}-[0-9]{1,6})(?![A-Za-z0-9])")

def detect_wbs(text):
    if not isinstance(text,str): return []
    return sorted(set(WBS_TOKEN.findall(text)))

def artifact_candidates(project,kind,source,external_id,title,url=None):
    if not isinstance(title,str): raise ValueError("title required")
    if url is not None and not url.startswith("https://"): raise ValueError("HTTPS URL required")
    return [{"reference_id":stable_id(project,wbs,kind,source,str(external_id)),
             "project_id":project,"wbs_id":wbs,"kind":kind,"source":source,
             "external_id":str(external_id),"url":url} for wbs in detect_wbs(title)]
