from pydantic import BaseModel,Field

class ParseNode(BaseModel):
    step_id:str
    event:str
    action:str
    depends_on:list[str]=Field(default_factory=list)