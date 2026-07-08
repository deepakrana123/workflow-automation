"""
app/evaluation/dataset.py

Loaders for evaluation ground truth datasets stored as JSON files.

Dataset format:
    A JSON file containing a list of expected workflow objects.

    [
      {
        "workflow_name": "Loan Approval",
        "expected_actions": ["run_cibil_check", "approve_loan", "disburse_loan"],
        "expected_triggers": ["loan_application_received"]
      },
      {
        "workflow_name": "Fraud Response",
        "expected_actions": ["aml_screening", "freeze_suspicious_account", "create_audit_record"],
        "expected_triggers": ["fraud_detected"]
      }
    ]

No example datasets are created here.
This module only deserializes JSON into the evaluation model types.
"""

import json
from pathlib import Path

from app.evaluation.evaluator import ExpectedWorkflow


def load_dataset(path: Path) -> list[ExpectedWorkflow]:
    """
    Load a ground truth evaluation dataset from a JSON file.

    The file must be a JSON array of objects, each containing:
      - workflow_name    (str)
      - expected_actions (list[str])
      - expected_triggers (list[str])

    Raises:
        FileNotFoundError: if the file does not exist
        ValueError: if the JSON structure is invalid or missing required fields
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError(
            f"Dataset must be a JSON array of workflow objects, got: {type(raw).__name__}"
        )

    workflows: list[ExpectedWorkflow] = []

    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(
                f"Item at index {i} must be a JSON object, got: {type(item).__name__}"
            )

        missing = [
            field
            for field in ("workflow_name", "expected_actions", "expected_triggers")
            if field not in item
        ]
        if missing:
            raise ValueError(
                f"Item at index {i} is missing required fields: {missing}"
            )

        if not isinstance(item["expected_actions"], list):
            raise ValueError(
                f"Item at index {i}: 'expected_actions' must be a list"
            )

        if not isinstance(item["expected_triggers"], list):
            raise ValueError(
                f"Item at index {i}: 'expected_triggers' must be a list"
            )

        workflows.append(
            ExpectedWorkflow(
                workflow_name=str(item["workflow_name"]),
                expected_actions=[str(a) for a in item["expected_actions"]],
                expected_triggers=[str(t) for t in item["expected_triggers"]],
            )
        )

    return workflows


def load_dataset_from_string(json_string: str) -> list[ExpectedWorkflow]:
    """
    Load a ground truth evaluation dataset from a JSON string.

    Useful for testing and in-memory evaluation without a file on disk.
    Applies the same validation as load_dataset().
    """
    try:
        raw = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    if not isinstance(raw, list):
        raise ValueError(
            f"Dataset must be a JSON array of workflow objects, got: {type(raw).__name__}"
        )

    tmp_path = Path("__in_memory__")

    workflows: list[ExpectedWorkflow] = []

    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(
                f"Item at index {i} must be a JSON object, got: {type(item).__name__}"
            )

        missing = [
            field
            for field in ("workflow_name", "expected_actions", "expected_triggers")
            if field not in item
        ]
        if missing:
            raise ValueError(
                f"Item at index {i} is missing required fields: {missing}"
            )

        if not isinstance(item["expected_actions"], list):
            raise ValueError(
                f"Item at index {i}: 'expected_actions' must be a list"
            )

        if not isinstance(item["expected_triggers"], list):
            raise ValueError(
                f"Item at index {i}: 'expected_triggers' must be a list"
            )

        workflows.append(
            ExpectedWorkflow(
                workflow_name=str(item["workflow_name"]),
                expected_actions=[str(a) for a in item["expected_actions"]],
                expected_triggers=[str(t) for t in item["expected_triggers"]],
            )
        )

    return workflows
