from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List


class WorkflowCreate(BaseModel):
    name: str
    domain: str
    raw_input: str


class DebugParseRequest(BaseModel):
    raw_input: str


class WorkflowResponse(BaseModel):
    id: int
    name: str
    domain: str
    raw_input: str
    parsed_rule_json: Optional[Dict[str, Any]] = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# ── NL generation ─────────────────────────────────────────────────────────────

class WorkflowGenerateRequest(BaseModel):
    user_request: str   # natural language sentence
    name: str           # workflow name to store
    domain: str         # support | health | loan | payments | hr | logistics | ecommerce


class WorkflowGenerateResponse(BaseModel):
    workflow_id: int
    name: str
    domain: str
    dsl: str
    execution_plan: Dict[str, List[str]]
    parsed_rule_json: Optional[Dict[str, Any]] = None
