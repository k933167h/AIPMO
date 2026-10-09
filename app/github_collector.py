"""Read-only GitHub issue/PR collector with bounded pagination and safe URLs."""
import os
import re
import httpx
from fastapi import HTTPException

_REPO=re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
_API="https://api.github.com"

def collect_github(repo: str, token: str | None=None, client=None) -> dict:
    if not _REPO.fullmatch(repo) or ".." in repo:
        raise ValueError("invalid repository")
    token=token or os.environ.get("PMO_GITHUB_TOKEN")
    if not token:
        raise HTTPException(503,"GitHub read-only token not configured")
    headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28"}
    def fetch(path):
        try:
            response=client.get(f"{_API}/repos/{repo}/{path}",headers=headers,
                                params={"state":"all","per_page":100},timeout=15)
            response.raise_for_status()
            data=response.json()
            if not isinstance(data,list): raise ValueError("invalid GitHub response")
            return data
        except (httpx.HTTPError,ValueError) as exc:
            raise HTTPException(502,"GitHub upstream request failed") from exc
    owned=client is None
    if owned: client=httpx.Client(follow_redirects=False)
    try:
        issues=fetch("issues")
        prs=fetch("pulls")
    finally:
        if owned: client.close()
    tasks=[{"id":f"GH-{i['number']}","title":i.get("title",""),
            "state":i.get("state"),"url":i.get("html_url"),
            "labels":[label.get("name") for label in i.get("labels",[])]}
           for i in issues if "pull_request" not in i]
    changes=[{"id":f"PR-{p['number']}","title":p.get("title",""),
              "state":p.get("state"),"url":p.get("html_url"),
              "merged_at":p.get("merged_at")} for p in prs]
    return {"source":"github","repository":repo,"issues":tasks,"pull_requests":changes,
            "partial":len(issues)==100 or len(prs)==100,
            "counts":{"issues":len(tasks),"pull_requests":len(changes)}}
