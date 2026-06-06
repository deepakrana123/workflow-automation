from pydantic import BaseModel, Field
from typing import List



class TriggerNode(BaseModel):
    event:str


class StepNode(BaseModel):
    id:str
    action:str
    depends_on:List[str]=Field(default_factory=list)


class WorkflowAST(BaseModel):
    trigger:TriggerNode
    steps:List[StepNode]