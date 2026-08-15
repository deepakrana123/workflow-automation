"""Unit tests for the workspace v2-template prompt variable builder."""

from app.workflow.workspace_context import build_workspace_prompt_vars


def test_summary_includes_description_display_name_and_actors():
    result = build_workspace_prompt_vars(
        display_name="Personal Loan Approval",
        description="Handles personal loan applications end to end.",
        actors=["Applicant", "Loan Officer (approver)"],
        rules=["Applicant must pass KYC before approval."],
    )
    assert "Handles personal loan applications end to end." in result["workspace_summary"]
    assert "Workspace: Personal Loan Approval." in result["workspace_summary"]
    assert "Relevant actors: Applicant, Loan Officer (approver)." in result["workspace_summary"]


def test_business_rules_are_numbered():
    result = build_workspace_prompt_vars(
        display_name="WS",
        description=None,
        actors=[],
        rules=["Rule A.", "Rule B."],
    )
    assert result["business_rules"] == "1. Rule A.\n2. Rule B."


def test_no_rules_renders_placeholder():
    result = build_workspace_prompt_vars("WS", None, [], [])
    assert result["business_rules"] == "None specified."


def test_summary_without_description_or_actors():
    result = build_workspace_prompt_vars("WS", None, [], [])
    assert result["workspace_summary"] == "Workspace: WS."
