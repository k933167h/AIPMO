from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .engine import EvaluateRequest,evaluate
from .adapters import normalize
router=APIRouter(prefix="/api/v1/cdpf",tags=["CDPF"])
class IngestRequest(BaseModel):
    project_id:str=Field(min_length=1)
    source:str
    records:list[dict]=Field(max_length=10000)
def require_auth(key):
    from app.main import require_key
    require_key(key)
@router.post("/evaluate")
def evaluate_risk(body:EvaluateRequest,x_api_key:str|None=Header(default=None)):
    require_auth(x_api_key)
    try: return evaluate(body)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.post("/normalize")
def normalize_events(body:IngestRequest,x_api_key:str|None=Header(default=None)):
    require_auth(x_api_key)
    try: return {"project_id":body.project_id,"signals":[s.model_dump(mode="json") for s in normalize(body.source,body.records)]}
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(422,str(exc)) from exc

@router.post("/ingest")
def ingest_events(body:IngestRequest,x_api_key:str|None=Header(default=None)):
    require_auth(x_api_key)
    from .persistence import persist
    try:
        signals=normalize(body.source,body.records)
        return persist(body.project_id,signals)
    except (ValueError,TypeError,KeyError) as exc:
        raise HTTPException(422,str(exc)) from exc

@router.get("/projects/{project_id}/risk")
def get_project_risk(project_id:str,x_api_key:str|None=Header(default=None)):
    require_auth(x_api_key)
    from .persistence import project_risk
    return project_risk(project_id)
