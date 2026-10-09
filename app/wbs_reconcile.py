"""Normalize project tasks from Jira, Plane and GANTT-AX without mutating sources."""
import re

WBS_ID=re.compile(r"\\bWBS[-_: ]([A-Za-z0-9][A-Za-z0-9._-]{0,63})\\b",re.I)

def _wbs(value):
    match=WBS_ID.search(str(value or ""))
    return match.group(1) if match else None

def normalize_jira(issues):
    result=[]
    for issue in issues:
        fields=issue.get("fields") or {}
        key=issue.get("key")
        if not key: continue
        result.append({"source":"jira","source_id":str(key),"wbs_id":_wbs(fields.get("summary")),
                       "title":str(fields.get("summary") or ""),"status":(fields.get("status") or {}).get("name"),
                       "story_points":fields.get("customfield_10016")})
    return result

def normalize_plane(issues):
    result=[]
    for issue in issues:
        identifier=issue.get("id")
        if not identifier: continue
        title=str(issue.get("name") or "")
        result.append({"source":"plane","source_id":str(identifier),"wbs_id":_wbs(title),
                       "title":title,"status":issue.get("state"),"story_points":issue.get("estimate_point")})
    return result

def normalize_ganttax(tasks):
    result=[]
    for task in tasks:
        identifier=task.get("id")
        if identifier is None: continue
        title=str(task.get("name") or task.get("title") or "")
        result.append({"source":"ganttax","source_id":str(identifier),
                       "wbs_id":str(task.get("wbs_id") or identifier),
                       "title":title,"status":task.get("status"),"story_points":task.get("story_points")})
    return result

def reconcile_wbs(jira,plane,ganttax,github_links=None):
    records=normalize_jira(jira)+normalize_plane(plane)+normalize_ganttax(ganttax)
    for link in github_links or []:
        if link.get("wbs_id") and link.get("external_id"):
            records.append({"source":"github","source_id":str(link["external_id"]),
                            "wbs_id":str(link["wbs_id"]),"title":"","status":None,"story_points":None})
    groups={}
    unmatched=[]
    for record in records:
        if not record["wbs_id"]:
            unmatched.append(record)
        else:
            groups.setdefault(record["wbs_id"],[]).append(record)
    return {"work_items":[{"wbs_id":key,"sources":value,
                           "source_count":len(value),"needs_review":len({x["source"] for x in value})!=len(value)}
                          for key,value in sorted(groups.items())],
            "unmatched":unmatched,"total_records":len(records)}
