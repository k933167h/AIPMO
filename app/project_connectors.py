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
