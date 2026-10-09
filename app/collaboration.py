"""Read-only collaboration adapters for air-gapped installations."""
import base64
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _base(url):
    parsed=urlsplit(url or "")
    if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("HTTPS collaboration URL required")
    return url.rstrip("/")

def _json_get(base,path,headers):
    req=Request(_base(base)+path,headers=headers,method="GET")
    with build_opener(_NoRedirect).open(req,timeout=10) as response:
        return json.load(response)

def _basic(user,token):
    if not user or not token: raise ValueError("credentials missing")
    return "Basic "+base64.b64encode(f"{user}:{token}".encode()).decode()

def zulip_channels():
    base=_base(os.getenv("PMO_ZULIP_URL"))
    headers={"Authorization":_basic(os.getenv("PMO_ZULIP_EMAIL"),os.getenv("PMO_ZULIP_API_KEY"))}
    payload=_json_get(base,"/api/v1/streams",headers)
    if payload.get("result")!="success" or not isinstance(payload.get("streams"),list):
        raise ValueError("unexpected Zulip response")
    return [{"id":s.get("stream_id"),"name":s.get("name")} for s in payload["streams"]]

def nextcloud_capabilities():
    base=_base(os.getenv("PMO_NEXTCLOUD_URL"))
    headers={"Authorization":_basic(os.getenv("PMO_NEXTCLOUD_USER"),os.getenv("PMO_NEXTCLOUD_APP_PASSWORD")),
             "OCS-APIRequest":"true","Accept":"application/json"}
    payload=_json_get(base,"/ocs/v2.php/cloud/capabilities?format=json",headers)
    if not isinstance(payload.get("ocs"),dict): raise ValueError("unexpected Nextcloud response")
    return payload["ocs"].get("data",{}).get("capabilities",{})

def docmost_integration_status():
    base=_base(os.getenv("PMO_DOCMOST_URL"))
    # Community edition has no supported public REST API. Do not call private frontend endpoints.
    return {"configured":bool(base),"rest_api":"enterprise_license_required",
            "mode":"manual_link_only"}
