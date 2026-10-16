from datetime import datetime, timezone
from pydantic import BaseModel, Field
WEIGHTS={"expectation":.25,"quality":.20,"schedule":.15,"communication":.15,"adoption":.15,"ai_trust":.10}
class Signal(BaseModel):
    source:str=Field(min_length=1)
    source_id:str=Field(min_length=1)
    dimension:str
    severity:float=Field(ge=0,le=100)
    observed_at:datetime
class EvaluateRequest(BaseModel):
    project_id:str=Field(min_length=1)
    signals:list[Signal]=Field(default_factory=list,max_length=10000)
def evaluate(body:EvaluateRequest):
    events={(s.source,s.source_id):s for s in body.signals}
    invalid=set(s.dimension for s in events.values())-set(WEIGHTS)
    if invalid: raise ValueError(f"unknown dimensions: {sorted(invalid)}")
    values={d:[s.severity for s in events.values() if s.dimension==d] for d in WEIGHTS}
    scores={d:round(sum(v)/len(v),2) if v else None for d,v in values.items()}
    coverage=round(sum(WEIGHTS[d] for d,v in scores.items() if v is not None),2)
    risk=round(sum(WEIGHTS[d]*v for d,v in scores.items() if v is not None)/coverage,2) if coverage else None
    level="unknown" if risk is None else "high" if risk>=70 else "watch" if risk>=40 else "normal"
    return {"project_id":body.project_id,"risk_score":risk,"level":level,"coverage":coverage,"dimensions":scores,"evidence_count":len(events),"evaluated_at":datetime.now(timezone.utc).isoformat()}
