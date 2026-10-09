"""Explicitly triggered read-only synchronization worker."""
from app.project_connectors import read_jira_pages,read_plane_pages
from app.sync_ingest import persist_items
from app.sync_policy import check_project_access

def sync_provider(provider,project_key,workspace=None,max_pages=3):
    check_project_access(project_key)
    if provider=="jira":
        records=read_jira_pages(project_key,max_pages=max_pages)
    elif provider=="plane":
        if not workspace: raise ValueError("Plane workspace required")
        records=read_plane_pages(workspace,project_key,max_pages=max_pages)
    else:
        raise ValueError("unsupported provider")
    if len(records)>=100*max_pages:
        raise ValueError("page cap reached; collection completeness unknown")
    return persist_items(project_key,provider,records,complete=True)
