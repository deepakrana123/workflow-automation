from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any


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
