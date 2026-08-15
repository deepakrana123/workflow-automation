# BRD Ingestion Pipeline

## Overview

Converts uploaded Banking Business Requirement Documents (PDFs) into structured workflow knowledge that can be mapped to the banking action catalog.

## Entry Point

```
POST /api/knowledge-ingestion/upload
Content-Type: multipart/form-data
Body: file (PDF)
```

## Pipeline Stages

### Stage 1 — Document Extraction
`DocumentExtractor` reads the PDF:
1. **PyPDF** — fast text extraction for digital PDFs
2. **OCR fallback** — Tesseract + pdf2image/Poppler for scanned documents

### Stage 2 — LLM Extraction
`WorkflowExtractor` calls Gemini with the extraction prompt to identify:
- `workflow_name` — what the workflow does
- `summary` — brief description
- `triggers` — business events that start the workflow
- `action_references` — operations the system performs
- `business_rules` — conditional logic
- `actors` — people/roles involved
- `external_systems` — systems referenced

Returns a validated `WorkflowExtraction` Pydantic model.

### Stage 3 — Persistence
`WorkflowRepository.save()` creates:
- `WorkflowKnowledge` record
- `WorkflowTriggerMapping` per extracted trigger
- `WorkflowActionMapping` per extracted action
- `WorkflowBusinessRule`, `WorkflowActor`, `WorkflowExternalSystem`

### Stage 4 — Embedding Mapping
`EmbeddingMapper` runs the full retrieval pipeline for each extracted action/trigger:
1. Encodes extracted name using embedding model
2. Runs vector search + BM25 + PostgreSQL full-text search
3. Fuses results with Reciprocal Rank Fusion (RRF)
4. Re-ranks with cross-encoder
5. Applies confidence threshold via MappingDecisionEngine

Updates `matched_action_definition_id` / `matched_trigger_definition_id` on mapping rows.

### Stage 5 — Action Configuration Initialization
Creates default `ActionConfiguration` rows for every successfully mapped action:
```json
{
  "execution_type": "python",
  "configuration": {"handler": "<handler_name_from_catalog>"}
}
```

## Key Files

| File | Responsibility |
|------|---------------|
| `app/knowledge_ingestions/service.py` | Orchestrates the full pipeline |
| `app/knowledge_ingestions/extractor.py` | PDF text extraction |
| `app/knowledge_ingestions/worfklow_extractors.py` | LLM-based workflow extraction |
| `app/knowledge_ingestions/workflow_repository.py` | Persistence + search queries |
| `app/knowledge_ingestions/embedding_mapper.py` | Semantic matching to catalog |
| `app/retrieval/pipeline.py` | Full retrieval stack orchestration |
