"""Read-only GitHub project data normalization for PMO reporting.

External GitHub API retrieval is deliberately separate; caller passes fetched
data, and this module never performs privileged write operations.
"""
from datetime import datetime,timezone

def _timestamp(value):
    if not value: return None
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc).isoformat()
    except (ValueError,TypeError,AttributeError): return None

def normalize_issues(items):
    result=[]
    for item in items:
        if "pull_request" in item: continue
        number=item.get("number")
        if not isinstance(number,int): continue
        result.append({"external_id":f"github:issue:{number}",
                       "type":"issue","number":number,"title":str(item.get("title") or ""),
                       "state":item.get("state"),"url":item.get("html_url"),
                       "assignee":(item.get("assignee") or {}).get("login"),
                       "labels":[x.get("name") for x in item.get("labels",[]) if isinstance(x,dict)],
                       "updated_at":_timestamp(item.get("updated_at"))})
    return result

def normalize_pull_requests(items):
    result=[]
    for item in items:
        number=item.get("number")
        if not isinstance(number,int): continue
        result.append({"external_id":f"github:pr:{number}",
                       "type":"pull_request","number":number,"title":str(item.get("title") or ""),
                       "state":item.get("state"),"draft":bool(item.get("draft",False)),
                       "merged":bool(item.get("merged_at")),
                       "url":item.get("html_url"),"updated_at":_timestamp(item.get("updated_at"))})
    return result

def normalize_workflow_runs(items):
    result=[]
    for item in items:
        identifier=item.get("id")
        if not isinstance(identifier,int): continue
        result.append({"external_id":f"github:ci:{identifier}","type":"ci_run",
                       "run_id":identifier,"name":item.get("name"),
                       "status":item.get("status"),"conclusion":item.get("conclusion"),
                       "head_sha":item.get("head_sha"),"url":item.get("html_url"),
                       "updated_at":_timestamp(item.get("updated_at"))})
    return result

def project_snapshot(issues,prs,runs):
    normalized={"issues":normalize_issues(issues),
                "pull_requests":normalize_pull_requests(prs),
                "workflow_runs":normalize_workflow_runs(runs)}
    normalized["summary"]={"open_issues":sum(x["state"]=="open" for x in normalized["issues"]),
        "open_prs":sum(x["state"]=="open" for x in normalized["pull_requests"]),
        "failed_ci_runs":sum(x["conclusion"]=="failure" for x in normalized["workflow_runs"])}
    return normalized
