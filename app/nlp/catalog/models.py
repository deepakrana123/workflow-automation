from dataclasses import dataclass
from typing import List

@dataclass
class CatalogMatchResult:
    workflow_type:str | None
    triggers:List[str]
    actions:List[str]
