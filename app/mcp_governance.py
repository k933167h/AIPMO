"""Fail-closed MCP tool governance; no remote tools are executed here."""
from typing import Literal
from pydantic import BaseModel, Field

class ToolPolicy(BaseModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9_.-]{3,100}$")
    operation: Literal["read","write","approve","deploy"]
    connector: str
    required_roles: list[str] = Field(min_length=1)
    requires_approval: bool = True

CATALOG = {
 "github.issues.read": ToolPolicy(name="github.issues.read",operation="read",connector="github",required_roles=["PM","PL","AUDITOR"],requires_approval=False),
 "github.pr.read": ToolPolicy(name="github.pr.read",operation="read",connector="github",required_roles=["PM","PL","QA","AUDITOR"],requires_approval=False),
 "github.pr.merge": ToolPolicy(name="github.pr.merge",operation="write",connector="github",required_roles=["PM","PL"]),
 "pmo.baseline.approve": ToolPolicy(name="pmo.baseline.approve",operation="approve",connector="aipmo",required_roles=["SME"]),
 "pmo.schedule.read": ToolPolicy(name="pmo.schedule.read",operation="read",connector="aipmo",required_roles=["PM","PL","AUDITOR"],requires_approval=False),
}

def authorize_tool(tool_name: str, roles: list[str], approved: bool=False) -> dict:
    policy=CATALOG.get(tool_name)
    if policy is None:
        return {"allowed":False,"reason":"tool not allowlisted"}
    if not set(roles).intersection(policy.required_roles):
        return {"allowed":False,"reason":"insufficient role"}
    if policy.requires_approval and not approved:
        return {"allowed":False,"reason":"human approval required"}
    return {"allowed":True,"tool":tool_name,"operation":policy.operation,"connector":policy.connector}
