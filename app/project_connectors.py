"""Read-only project connector utilities."""

from app.wbs_reconcile import reconcile_wbs


def reconcile_external_work(jira, plane, ganttax=None, github_links=None):
    return reconcile_wbs(jira, plane, ganttax or [], github_links or [])

import json
import os
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

def _base_url(value):
    parts = urlsplit(value or "")
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("valid HTTPS service URL required")
    return value.rstrip("/")

def _request_json(url, headers):
    with urlopen(Request(url, headers=headers), timeout=10) as response:
        return json.load(response)

def read_jira(project_key, base_url=None, email=None, token=None):
    import base64
    if not project_key or not project_key.replace("-", "").replace("_", "").isalnum():
        raise ValueError("invalid Jira project key")
    base = _base_url(base_url or os.environ.get("PMO_JIRA_URL"))
    email = email or os.environ.get("PMO_JIRA_EMAIL")
    token = token or os.environ.get("PMO_JIRA_TOKEN")
    if not email or not token:
        raise ValueError("Jira credentials missing")
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    query = urlencode({"jql": f'project = "{project_key}" ORDER BY updated DESC', "maxResults": 100,
                       "fields": "summary,status,customfield_10016"})
    payload = _request_json(f"{base}/rest/api/3/search?{query}",
                            {"Authorization": f"Basic {auth}", "Accept": "application/json"})
    if not isinstance(payload, dict) or not isinstance(payload.get("issues"), list):
        raise ValueError("unexpected Jira response")
    return payload["issues"]

def read_plane(workspace, project_id, base_url=None, token=None):
    for value in (workspace, project_id):
        if not isinstance(value, str) or not value or not all(ch.isalnum() or ch in "-_" for ch in value):
            raise ValueError("invalid Plane project identifier")
    base = _base_url(base_url or os.environ.get("PMO_PLANE_URL"))
    token = token or os.environ.get("PMO_PLANE_TOKEN")
    if not token:
        raise ValueError("Plane credential missing")
    url = f"{base}/api/v1/workspaces/{workspace}/projects/{project_id}/issues/?{urlencode({'per_page': 100})}"
    payload = _request_json(url, {"X-API-Key": token, "Accept": "application/json"})
    issues = payload.get("results") if isinstance(payload, dict) else payload
    if not isinstance(issues, list):
        raise ValueError("unexpected Plane response")
    return issues
