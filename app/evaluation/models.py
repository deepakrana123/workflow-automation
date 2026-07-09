"""
app/evaluation/models.py

Pydantic models for the MFlows evaluation framework.

These models represent the result of comparing extracted workflow knowledge
(from the ingestion pipeline) against expected ground truth from annotated BRDs.

They are read-only evaluation artefacts. They do not interact with the database,
the ingestion pipeline, or the execution engine.
"""

from pydantic import BaseModel, Field


class RankingCandidate(BaseModel):
    """
    A single candidate from the hybrid retriever with per-source rank breakdown.

    name           — catalog name of the candidate
    rrf_score      — fused Reciprocal Rank Fusion score
    vector_rank    — rank from vector (embedding) retriever, None if not retrieved
    bm25_rank      — rank from BM25 keyword retriever, None if not retrieved
    postgres_rank  — rank from Postgres full-text retriever, None if not retrieved
    """

    name: str
    rrf_score: float
    vector_rank: int | None = None
    bm25_rank: int | None = None
    postgres_rank: int | None = None


class ActionEvaluation(BaseModel):
    """
    Evaluation result for a single extracted action reference.

    extracted_action  — the raw name extracted from the BRD by the LLM
    expected_action   — the canonical action name from the ground truth dataset
    predicted_action  — the action name the embedding mapper matched in the catalog
                        (None if no match was found)
    similarity_score  — RRF score of the top candidate (0.0–1.0)
                        None if no match was attempted or found
    correct           — True if predicted_action is in the expected set
    expected_rank     — rank at which the expected action appeared in the
                        retriever candidates list (None if not found in top-N)
    top_candidates    — ranked list of top-N retriever candidates with score breakdown
    """

    extracted_action: str
    expected_action: str
    predicted_action: str | None
    similarity_score: float | None
    correct: bool
    expected_rank: int | None = None
    top_candidates: list[RankingCandidate] = Field(default_factory=list)


class TriggerEvaluation(BaseModel):
    """
    Evaluation result for a single extracted trigger.

    extracted_trigger  — the raw name extracted from the BRD by the LLM
    expected_trigger   — the canonical trigger name from the ground truth dataset
    predicted_trigger  — the trigger name the embedding mapper matched in the catalog
                         (None if no match was found)
    similarity_score   — RRF score of the top candidate (0.0–1.0)
                         None if no match was attempted or found
    correct            — True if predicted_trigger is in the expected set
    expected_rank      — rank at which the expected trigger appeared in the
                         retriever candidates list (None if not found in top-N)
    top_candidates     — ranked list of top-N retriever candidates with score breakdown
    """

    extracted_trigger: str
    expected_trigger: str
    predicted_trigger: str | None
    similarity_score: float | None
    correct: bool
    expected_rank: int | None = None
    top_candidates: list[RankingCandidate] = Field(default_factory=list)


class WorkflowEvaluation(BaseModel):
    """
    Evaluation result for a single workflow extracted from a BRD.

    workflow_name     — name of the workflow as extracted
    action_results    — one ActionEvaluation per extracted action reference
    trigger_results   — one TriggerEvaluation per extracted trigger
    """

    workflow_name: str
    action_results: list[ActionEvaluation] = Field(default_factory=list)
    trigger_results: list[TriggerEvaluation] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    """
    Aggregated evaluation metrics across one or more workflows.

    total_workflows      — number of workflows evaluated
    total_actions        — total action evaluations across all workflows
    total_triggers       — total trigger evaluations across all workflows
    action_accuracy      — fraction of actions where predicted is in the expected set (0.0–1.0)
    trigger_accuracy     — fraction of triggers where predicted is in the expected set (0.0–1.0)
    average_similarity   — mean RRF score of the top candidate across all mappings
                           (excludes entries where similarity_score is None)
    unknown_actions      — count of actions where predicted_action is None
    unknown_triggers     — count of triggers where predicted_trigger is None
    mean_reciprocal_rank_actions   — MRR across all action queries (0.0–1.0)
    mean_reciprocal_rank_triggers  — MRR across all trigger queries (0.0–1.0)
    workflow_results     — per-workflow breakdown
    """

    total_workflows: int
    total_actions: int
    total_triggers: int
    action_accuracy: float
    trigger_accuracy: float
    average_similarity: float
    unknown_actions: int
    unknown_triggers: int
    mean_reciprocal_rank_actions: float = 0.0
    mean_reciprocal_rank_triggers: float = 0.0
    workflow_results: list[WorkflowEvaluation] = Field(default_factory=list)
