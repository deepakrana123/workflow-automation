"""
app/prompting/prompt_evaluation.py

Data class for tracking prompt performance metrics.
"""

from dataclasses import dataclass


@dataclass
class PromptEvaluation:
    prompt_version: str
    success: bool
    latency_ms: int
    provider: str
