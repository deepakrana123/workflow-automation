"""
app/context_assembly

Context assembly and source traceability layer for Phase 5.

Responsibilities:
- Convert hybrid retrieval results into structured context with provenance
- Validate tenant/workspace ownership and isolation
- Track token budgets and manage exclusions
- Preserve and validate source provenance chains
- Detect and preserve conflicting rules (no auto-resolution)
- Provide complete metadata for LLM consumption and debugging

Public API:
- ContextAssemblyService — main service for context assembly
- AssembledContext, SelectedBusinessRule, SourceProvenance — DTOs
"""

from app.context_assembly.models import (
    AssembledContext,
    SelectedBusinessRule,
    SourceProvenance,
)
from app.context_assembly.context_assembler import ContextAssemblyService

__all__ = [
    "ContextAssemblyService",
    "AssembledContext",
    "SelectedBusinessRule",
    "SourceProvenance",
]
