from dataclasses import dataclass
from typing import Any

@dataclass

class RetrievalCandidate:
    entity:Any
    vector_score:float | None =None
    keyword_score:float | None=None
    rrf_score:float | None =None