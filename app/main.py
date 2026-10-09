import os
from typing import Any
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from app.engine import progress, evm
from app.schedule import critical_path
from app.calendar import project_schedule_dates
from app.baseline import compare_baseline
from app.approvals import propose_baseline, approve_baseline, load_approved_baseline

app = FastAPI(title="AI PMO Starter API", version="1.8.0")
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
def approve_staged_baseline(baseline_id:str,data:BaselineApproval,x_api_key:str|None=Header(default=None)):
    require_key(x_api_key)
    try: result=approve_baseline(baseline_id,data.reviewer)
    except ValueError as exc: raise HTTPException(422,str(exc))
    if result is None: raise HTTPException(404,"staged baseline not found")
    return result
