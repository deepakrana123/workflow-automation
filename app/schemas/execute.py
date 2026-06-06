from pydantic import BaseModel
from typing import Dict, Any


class ExecuteWorkflow(BaseModel):
    workflow_id: int
    entity_id: str
