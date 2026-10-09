import os
import secrets
from typing import Any
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from app.engine import progress, evm
from app.schedule import critical_path
from app.calendar import project_schedule_dates
from app.baseline import compare_baseline
from app.approvals import propose_baseline, approve_baseline, load_approved_baseline, audit_events, audit_integrity, reject_baseline
from app.identity import resolve_identity
from app.oidc import verify_oidc

app = FastAPI(title="AI PMO Starter API", version="3.8.0")
class Task(BaseModel):
    weight: float = Field(gt=0)
    completion: float = Field(ge=0, le=1)
class ProgressRequest(BaseModel):
    tasks: list[Task]
class EVMRequest(BaseModel):
    pv: float = Field(ge=0)
    ev: float = Field(ge=0)
    ac: float = Field(ge=0)
    bac: float = Field(ge=0)
class ScheduleTask(BaseModel):
    id: str = Field(min_length=1)
    duration: float = Field(ge=0)
    predecessors: list[str | dict[str, Any]] = Field(default_factory=list)
class ScheduleRequest(BaseModel):
    tasks: list[ScheduleTask]
    project_start: str | None = None
    holidays: list[str] = Field(default_factory=list)
    working_weekdays: list[int] = Field(default_factory=lambda: [0,1,2,3,4])
    baseline: dict[str, Any] | None = None
    baseline_id: str | None = None
@app.get("/health")
def health(): return {"status":"ok"}
def require_key(key):
    expected=os.environ.get("PMO_API_KEY")
    if not expected or key!=expected: raise HTTPException(401,"unauthorized")
@app.post("/api/v1/progress")
def calc_progress(data:ProgressRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    return {"progress_pct":progress([t.model_dump() for t in data.tasks])}
@app.post("/api/v1/evm")
def calc_evm(data:EVMRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    return evm(**data.model_dump())
@app.post("/api/v1/ganttax/imports",status_code=201)
def import_ganttax(data:dict[str,Any],x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    from app.store import stage_import
    try: return stage_import(data)
    except (ValueError,TypeError) as exc: raise HTTPException(422,str(exc))
@app.get("/api/v1/ganttax/imports/{import_id}/export")
def export_ganttax(import_id:str,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    from app.store import export_import
    data=export_import(import_id)
    if data is None: raise HTTPException(404,"import not found")
    return data
@app.post("/api/v1/schedule/cpm")
def calculate_cpm(data:ScheduleRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try:
        result=critical_path([t.model_dump() for t in data.tasks])
        if data.baseline_id and data.baseline is not None:
            raise ValueError('provide baseline_id instead of baseline for persisted approval')
        if data.baseline_id:
            approved=load_approved_baseline(data.baseline_id)
            if approved is None: raise HTTPException(404,'approved baseline not found')
            data.baseline=approved
        if data.baseline is not None and not data.project_start:
            raise ValueError('project_start required for baseline comparison')
        dated=project_schedule_dates(result,data.project_start,data.holidays,data.working_weekdays) if data.project_start else result
        if data.baseline is not None:
            dated['baseline_variance']=compare_baseline(dated,data.baseline)
        return dated
    except ValueError as exc: raise HTTPException(422,str(exc))

class BaselineProposal(BaseModel):
    project_code: str = Field(min_length=1)
    baseline: dict[str,Any]
class BaselineApproval(BaseModel):
    reviewer: str = Field(min_length=1)
@app.post("/api/v1/baselines",status_code=201)
def create_baseline(data:BaselineProposal,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try: return propose_baseline(data.project_code,data.baseline)
    except ValueError as exc: raise HTTPException(422,str(exc))
@app.post("/api/v1/baselines/{baseline_id}/approve")
def approve_staged_baseline(baseline_id:str,data:BaselineApproval,x_api_key:str|None=Header(default=None),x_sme_key:str|None=Header(default=None),x_identity_token:str|None=Header(default=None)):
    require_key(x_api_key)
    approval_key=os.environ.get("PMO_SME_APPROVAL_KEY")
    if not approval_key or not secrets.compare_digest(x_sme_key or "",approval_key):
        raise HTTPException(403,"SME approval credential required")
    actor=verify_oidc(x_identity_token,"SME") if os.environ.get("PMO_AUTH_MODE")=="oidc" else resolve_identity(x_identity_token,"SME")
    if data.reviewer!=actor: raise HTTPException(403,"reviewer identity mismatch")
    try: result=approve_baseline(baseline_id,actor)
    except ValueError as exc: raise HTTPException(422,str(exc))
    if result is None: raise HTTPException(404,"staged baseline not found")
    return result

@app.get("/api/v1/baselines/{baseline_id}/audit")
def baseline_audit(baseline_id:str,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    return {"baseline_id":baseline_id,"events":audit_events(baseline_id)}

class BaselineRejection(BaseModel):
    reason: str = Field(min_length=1)
@app.post("/api/v1/baselines/{baseline_id}/reject")
def reject_staged_baseline(baseline_id:str,data:BaselineRejection,x_api_key:str|None=Header(default=None),x_sme_key:str|None=Header(default=None),x_identity_token:str|None=Header(default=None)):
    require_key(x_api_key)
    approval_key=os.environ.get("PMO_SME_APPROVAL_KEY")
    if not approval_key or not secrets.compare_digest(x_sme_key or "",approval_key):
        raise HTTPException(403,"SME approval credential required")
    actor=resolve_identity(x_identity_token,"SME")
    try: result=reject_baseline(baseline_id,actor,data.reason)
    except ValueError as exc: raise HTTPException(422,str(exc))
    if result is None: raise HTTPException(404,"staged baseline not found")
    return result

@app.get("/api/v1/baselines/{baseline_id}/audit/verify")
def verify_baseline_audit(baseline_id:str,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    return {"baseline_id":baseline_id,**audit_integrity(baseline_id)}

from app.mcp_governance import CATALOG,authorize_tool

@app.get("/api/v1/mcp/tools")
def list_mcp_tools(x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    return {"tools":[policy.model_dump() for policy in CATALOG.values()]}

class MCPAuthorizationRequest(BaseModel):
    tool_name: str
    roles: list[str] = Field(default_factory=list)
    approved: bool = False

@app.post("/api/v1/mcp/policy/check")
def check_mcp_policy(data:MCPAuthorizationRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    return authorize_tool(data.tool_name,data.roles,data.approved)

from app.github_sync import project_snapshot

class GitHubSnapshotRequest(BaseModel):
    issues: list[dict[str,Any]] = Field(default_factory=list)
    pull_requests: list[dict[str,Any]] = Field(default_factory=list)
    workflow_runs: list[dict[str,Any]] = Field(default_factory=list)

@app.post("/api/v1/integrations/github/snapshot")
def normalize_github_snapshot(data:GitHubSnapshotRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    return project_snapshot(data.issues,data.pull_requests,data.workflow_runs)

from app.github_reader import fetch_github_snapshot

@app.get("/api/v1/integrations/github/{owner}/{repo}/sync")
def sync_github_repository(owner:str,repo:str,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try: return fetch_github_snapshot(f"{owner}/{repo}")
    except ValueError as exc: raise HTTPException(422,str(exc))
    except RuntimeError as exc: raise HTTPException(502,str(exc))

from app.wbs_reconcile import reconcile_wbs

class WBSReconciliationRequest(BaseModel):
    jira: list[dict[str,Any]] = Field(default_factory=list)
    plane: list[dict[str,Any]] = Field(default_factory=list)
    ganttax: list[dict[str,Any]] = Field(default_factory=list)
    github_links: list[dict[str,Any]] = Field(default_factory=list)

@app.post("/api/v1/wbs/reconcile")
def reconcile_project_wbs(data:WBSReconciliationRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    return reconcile_wbs(data.jira,data.plane,data.ganttax,data.github_links)

from app.project_connectors import read_jira, read_plane, reconcile_external_work

class ExternalWBSRequest(BaseModel):
    jira_project: str
    plane_workspace: str
    plane_project: str
    ganttax: list[dict[str,Any]] = Field(default_factory=list)
    github_links: list[dict[str,Any]] = Field(default_factory=list)

@app.post("/api/v1/wbs/reconcile/remote")
def reconcile_remote_wbs(data:ExternalWBSRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try:
        jira = read_jira(data.jira_project)
        plane = read_plane(data.plane_workspace,data.plane_project)
        return reconcile_external_work(jira,plane,data.ganttax,data.github_links)
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    except Exception:
        raise HTTPException(502,"remote project service unavailable")

from app.project_connectors import read_project_pages

class PagedWBSRequest(BaseModel):
    jira_project: str
    plane_workspace: str
    plane_project: str
    max_pages: int = Field(default=3,ge=1,le=5)
    ganttax: list[dict[str,Any]] = Field(default_factory=list)
    github_links: list[dict[str,Any]] = Field(default_factory=list)

@app.post("/api/v1/wbs/reconcile/paged")
def reconcile_paged_wbs(data:PagedWBSRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try:
        remote=read_project_pages(data.jira_project,data.plane_workspace,data.plane_project,data.max_pages)
        result=reconcile_external_work(remote["jira"],remote["plane"],data.ganttax,data.github_links)
        result["source_counts"]={"jira":remote["jira_count"],"plane":remote["plane_count"]}
        return result
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    except Exception:
        raise HTTPException(502,"remote project service unavailable")

from app.sync_policy import check_project_access, changed_since

class DeltaWBSRequest(BaseModel):
    jira_project: str
    plane_workspace: str
    plane_project: str
    max_pages: int = Field(default=3,ge=1,le=5)
    updated_since: str | None = None

@app.post("/api/v1/wbs/changes")
def read_wbs_changes(data:DeltaWBSRequest,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try:
        check_project_access(data.jira_project)
        check_project_access(data.plane_project)
        remote=read_project_pages(data.jira_project,data.plane_workspace,data.plane_project,data.max_pages)
        jira=changed_since([dict(issue,updated=(issue.get("fields") or {}).get("updated")) for issue in remote["jira"]],data.updated_since)
        plane=changed_since(remote["plane"],data.updated_since)
        return {"jira":jira,"plane":plane,"bounded":True}
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    except Exception:
        raise HTTPException(502,"remote project service unavailable")

from app.sync_checkpoints import read_checkpoint,record_sync

class SyncRunRecord(BaseModel):
    project_key: str
    provider: str
    watermark: datetime | None = None
    observed_count: int = Field(ge=0)
    success: bool = True
    error_code: str | None = None

@app.post("/api/v1/sync/runs")
def save_sync_run(data:SyncRunRecord,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try:
        check_project_access(data.project_key)
        return record_sync(data.project_key,data.provider,data.watermark,
                           data.observed_count,data.success,data.error_code)
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))

@app.get("/api/v1/sync/checkpoints/{provider}/{project_key}")
def get_sync_checkpoint(provider:str,project_key:str,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try:
        check_project_access(project_key)
        return {"project_key":project_key,"provider":provider,
                "watermark":read_checkpoint(project_key,provider)}
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))

from app.sync_worker import sync_provider

class WorkerSyncRequest(BaseModel):
    provider: str
    project_key: str
    workspace: str | None = None
    max_pages: int = Field(default=3,ge=1,le=5)

@app.post("/api/v1/sync/execute")
def execute_project_sync(data:WorkerSyncRequest,x_api_key:str|None=Header(default=None),
                         x_worker_key:str|None=Header(default=None)):
    require_key(x_api_key)
    expected=os.getenv("PMO_SYNC_WORKER_KEY")
    if not expected or not x_worker_key or not secrets.compare_digest(expected,x_worker_key):
        raise HTTPException(403,"worker authorization required")
    try:
        return sync_provider(data.provider,data.project_key,data.workspace,data.max_pages)
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    except Exception:
        raise HTTPException(502,"sync execution failed")

from app.collaboration import zulip_channels,nextcloud_capabilities,docmost_integration_status

@app.get("/api/v1/collaboration/{provider}/probe")
def probe_collaboration(provider:str,x_api_key:str|None=Header(default=None),
                        x_worker_key:str|None=Header(default=None)):
    require_key(x_api_key)
    expected=os.getenv("PMO_SYNC_WORKER_KEY")
    if not expected or not x_worker_key or not secrets.compare_digest(expected,x_worker_key):
        raise HTTPException(403,"integration worker authorization required")
    try:
        if provider=="zulip":
            channels=zulip_channels()
            return {"provider":provider,"channel_count":len(channels),"channels":channels}
        if provider=="nextcloud":
            capabilities=nextcloud_capabilities()
            return {"provider":provider,"capability_keys":sorted(capabilities)}
        if provider=="docmost":
            return {"provider":provider,**docmost_integration_status()}
        raise HTTPException(404,"unknown collaboration provider")
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502,"collaboration service unavailable")

from app.artifact_store import register,list_links

class ArtifactLinkRequest(BaseModel):
    project_id: str = Field(min_length=1)
    wbs_id: str = Field(min_length=1)
    kind: str
    source: str = Field(min_length=1)
    external_id: str = Field(min_length=1)
    url: str | None = None
    metadata: dict[str,Any] = Field(default_factory=dict)

def _artifact_worker_auth(api_key,worker_key):
    require_key(api_key)
    expected=os.getenv("PMO_SYNC_WORKER_KEY")
    if not expected or not worker_key or not secrets.compare_digest(expected,worker_key):
        raise HTTPException(403,"artifact worker authorization required")

@app.post("/api/v1/artifacts/links")
def add_artifact_link(data:ArtifactLinkRequest,x_api_key:str|None=Header(default=None),
                      x_worker_key:str|None=Header(default=None)):
    _artifact_worker_auth(x_api_key,x_worker_key)
    try:
        check_project_access(data.project_id)
        return register(data.project_id,data.wbs_id,data.kind,data.source,
                        data.external_id,data.url,data.metadata)
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))

@app.get("/api/v1/artifacts/{project_id}/{wbs_id}")
def get_artifact_links(project_id:str,wbs_id:str,limit:int=100,
                       x_api_key:str|None=Header(default=None),
                       x_worker_key:str|None=Header(default=None)):
    _artifact_worker_auth(x_api_key,x_worker_key)
    try:
        check_project_access(project_id)
        return {"project_id":project_id,"wbs_id":wbs_id,"links":list_links(project_id,wbs_id,limit)}
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))

from app.collaboration_ingest import ingest_zulip,ingest_nextcloud

class CollaborationIngestRequest(BaseModel):
    project_id: str = Field(min_length=1)
    provider: str
    stream_id: int | None = None
    folder: str = ""

@app.post("/api/v1/collaboration/ingest")
def run_collaboration_ingest(data:CollaborationIngestRequest,
                             x_api_key:str|None=Header(default=None),
                             x_worker_key:str|None=Header(default=None)):
    _artifact_worker_auth(x_api_key,x_worker_key)
    try:
        if data.provider=="zulip":
            if data.stream_id is None: raise ValueError("stream_id required")
            return ingest_zulip(data.project_id,data.stream_id)
        if data.provider=="nextcloud":
            return ingest_nextcloud(data.project_id,data.folder)
        raise HTTPException(422,"provider ingestion unsupported")
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502,"collaboration ingestion failed")

from app.collaboration_sync import apply_batch,read_cursor

class SyncArtifactItem(BaseModel):
    wbs_id: str = Field(min_length=1)
    kind: str
    external_id: str = Field(min_length=1)
    metadata: dict[str,Any] = Field(default_factory=dict)

class CollaborationBatchRequest(BaseModel):
    project_id: str = Field(min_length=1)
    provider: str
    scope: str = Field(min_length=1)
    cursor: str | None = None
    items: list[SyncArtifactItem] = Field(max_length=500)

@app.post("/api/v1/collaboration/sync/batch")
def commit_collaboration_batch(data:CollaborationBatchRequest,
                                x_api_key:str|None=Header(default=None),
                                x_worker_key:str|None=Header(default=None)):
    _artifact_worker_auth(x_api_key,x_worker_key)
    try:
        check_project_access(data.project_id)
        return apply_batch(data.project_id,data.provider,data.scope,
                           [item.model_dump() for item in data.items],data.cursor)
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))

@app.get("/api/v1/collaboration/sync/cursor")
def collaboration_cursor(project_id:str,provider:str,scope:str,
                         x_api_key:str|None=Header(default=None),
                         x_worker_key:str|None=Header(default=None)):
    _artifact_worker_auth(x_api_key,x_worker_key)
    try:
        check_project_access(project_id)
        return {"cursor":read_cursor(project_id,provider,scope)}
    except PermissionError:
        raise HTTPException(403,"project not authorized")

from app.collaboration_delta_worker import run_zulip_delta
from app.collaboration_lock import run_exclusive

class ZulipDeltaRequest(BaseModel):
    project_id: str = Field(min_length=1)
    stream_id: int = Field(gt=0)
    limit: int = Field(default=100,ge=1,le=100)

@app.post("/api/v1/collaboration/sync/zulip-delta")
def execute_zulip_delta(data:ZulipDeltaRequest,
                        x_api_key:str|None=Header(default=None),
                        x_worker_key:str|None=Header(default=None)):
    _artifact_worker_auth(x_api_key,x_worker_key)
    try:
        return run_exclusive(data.project_id,"zulip",f"stream-{data.stream_id}",lambda:run_zulip_delta(data.project_id,data.stream_id,data.limit))
    except PermissionError:
        raise HTTPException(403,"project not authorized")
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    except Exception:
        raise HTTPException(502,"delta sync failed")
