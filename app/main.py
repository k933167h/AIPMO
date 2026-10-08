import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from app.engine import progress, evm

app = FastAPI(title="AI PMO Starter API", version="1.0.0")
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
