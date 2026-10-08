import os
from typing import Any
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from app.engine import progress, evm
from app.schedule import critical_path

app = FastAPI(title="AI PMO Starter API", version="1.5.0")
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
    try: return critical_path([t.model_dump() for t in data.tasks])
    except ValueError as exc: raise HTTPException(422,str(exc))
