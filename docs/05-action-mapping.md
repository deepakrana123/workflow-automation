# Action Mapping & Retrieval

## Overview

Maps extracted BRD text (e.g., "Validate customer identity documents") to canonical banking actions in the catalog (e.g., `verify_kyc_documents`) using a multi-stage retrieval pipeline.

## Retrieval Pipeline

```
Extracted Action Name
    ↓
┌─────────────────────────────────────────────────┐
│         Three Parallel Retrievers               │
│                                                 │
│  Vector Search    BM25 Keywords    PG Full-Text │
│  (cosine dist)   (alias match)    (ts_rank)    │
└────────┬──────────────┬───────────────┬─────────┘
         └──────────────┼───────────────┘
                        ▼
              Reciprocal Rank Fusion (RRF)
                        ↓
              Cross-Encoder Re-Ranking
                        ↓
              MappingDecisionEngine
              (confidence threshold)
                        ↓
              Best Match or "Unknown"
```

## Components

### VectorRetriever
Queries `action_definitions.embedding` using pgvector cosine distance. Returns top-N candidates with distance scores.

### KeywordRetriever
Matches against `name`, `display_name`, and `aliases` JSONB array using substring matching.

### PostgressRetriever
PostgreSQL full-text search using `to_tsvector` / `plainto_tsquery` with `ts_rank` scoring.

### ReciprocalRankFusion
Combines results from all three retrievers using RRF formula:
```
score(d) = Σ 1 / (k + rank_i(d))
```
Where `k = 60` (standard constant).

### CrossEncoderReRanker
Re-scores top candidates using a cross-encoder model for precise semantic similarity.

### MappingDecisionEngine
Applies confidence thresholds to determine if the top candidate is a reliable match:
- Above threshold → return matched action
- Below threshold → return None (unknown/unmapped)

## Embedding Models

| Use Case | Model | Dimensions |
|----------|-------|-----------|
| Catalog embeddings (triggers/actions) | BAAI/bge-small-en-v1.5 | 384 |
| BRD extraction mapping | all-MiniLM-L6-v2 | 384 |

## Backfilling Embeddings

After adding new actions/triggers to the catalog:
```bash
python scripts/backfill_embeddings.py
```
