"""Read-only GitHub REST adapter with bounded pagination and WBS references."""
import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from app.github_sync import project_snapshot

REPO_PATTERN=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WBS_PATTERN=re.compile(r"\\bWBS[-_: ]([A-Za-z0-9][A-Za-z0-9._-]{0,63})\\b",re.I)

def fetch_github_snapshot(repo,token=None,pages=2,timeout=10):
    if not REPO_PATTERN.fullmatch(repo): raise ValueError("invalid repository")
    if not isinstance(pages,int) or not 1<=pages<=5: raise ValueError("pages must be 1..5")
    token=token or os.environ.get("PMO_GITHUB_READ_TOKEN")
    if not token: raise ValueError("PMO_GITHUB_READ_TOKEN required")
    owner,name=repo.split("/")
    root=f"https://api.github.com/repos/{owner}/{name}"
    def collect(path,params):
        items=[]
        for page in range(1,pages+1):
            query=urlencode({**params,"per_page":100,"page":page})
            request=Request(f"{root}/{path}?{query}",headers={
                "Authorization":f"Bearer {token}","Accept":"application/vnd.github+json",
                "X-GitHub-Api-Version":"2022-11-28","User-Agent":"AIPMO-read-adapter"})
            try:
                with urlopen(request,timeout=timeout) as response:
                    data=json.load(response)
            except (HTTPError,URLError,TimeoutError) as exc:
                raise RuntimeError("GitHub read failed") from exc
            if not isinstance(data,list): raise RuntimeError("unexpected GitHub response")
            items.extend(data)
            if len(data)<100: break
        return items
    issues=collect("issues",{"state":"all"})
    prs=collect("pulls",{"state":"all"})
    runs=collect("actions/runs",{}) if False else []
    snapshot=project_snapshot(issues,prs,runs)
    snapshot["repository"]=repo
    snapshot["wbs_links"]=map_wbs_links(snapshot)
    return snapshot

def map_wbs_links(snapshot):
    result=[]
    for collection in ("issues","pull_requests"):
        for item in snapshot.get(collection,[]):
            for match in WBS_PATTERN.finditer(item.get("title") or ""):
                result.append({"wbs_id":match.group(1),"external_id":item["external_id"],
                               "type":item["type"],"url":item.get("url")})
    return result
