"""Collaboration ingestion requires explicit project-scoped operator trigger."""
from urllib.parse import unquote
from app.collaboration_discovery import zulip_recent_messages,nextcloud_list_folder
from app.collaboration_mapping import artifact_candidates
from app.artifact_store import register
from app.sync_policy import check_project_access

def ingest_zulip(project,stream_id):
    check_project_access(project)
    messages=zulip_recent_messages(stream_id)
    created=[]
    for message in messages:
        title=str(message.get("subject") or "")
        for ref in artifact_candidates(project,"message","zulip",message.get("id"),title):
            created.append(register(project,ref["wbs_id"],"message","zulip",ref["external_id"]))
    return {"provider":"zulip","registered":len(created),"references":created}

def ingest_nextcloud(project,folder=""):
    check_project_access(project)
    items=nextcloud_list_folder(folder)
    created=[]
    for item in items:
        href=item["href"]
        title=unquote(href).rsplit("/",1)[-1]
        for ref in artifact_candidates(project,"file","nextcloud",href,title):
            created.append(register(project,ref["wbs_id"],"file","nextcloud",href))
    return {"provider":"nextcloud","registered":len(created),"references":created}
