"""Unit tests for the workspace-scoped catalog match assembly.

Pure function only — no DB. Uses lightweight fakes mimicking
ActionDefinition / TriggerDefinition (id, name, workflow_type).
"""

from dataclasses import dataclass

from app.nlp.catalog.workspace_catalog_matcher import build_workspace_match_result


@dataclass
class _Def:
    id: int
    name: str
    workflow_type: str | None = None


def test_actions_and_triggers_are_carried_through():
    actions = [_Def(1, "run_cibil_check", "loan"), _Def(2, "approve_loan", "loan")]
    triggers = [_Def(10, "loan_application_received", "loan")]
    result = build_workspace_match_result(actions, triggers)

    assert result.action_names == ["run_cibil_check", "approve_loan"]
    assert result.trigger_names == ["loan_application_received"]
    assert result.matched_actions == actions
    assert result.matched_triggers == triggers


def test_workflow_type_is_the_majority():
    actions = [_Def(1, "a", "loan"), _Def(2, "b", "loan"), _Def(3, "c", "payments")]
    result = build_workspace_match_result(actions, [])
    assert result.workflow_type == "loan"


def test_workflow_type_none_when_absent():
    actions = [_Def(1, "a", None)]
    result = build_workspace_match_result(actions, [])
    assert result.workflow_type is None


def test_selected_global_actions_are_added():
    actions = [_Def(1, "run_cibil_check", "loan")]
    selected = [_Def(99, "generate_pdf", "documents")]
    result = build_workspace_match_result(actions, [], selected_actions=selected)
    assert result.action_names == ["run_cibil_check", "generate_pdf"]


def test_selected_action_already_in_workspace_is_not_duplicated():
    actions = [_Def(1, "run_cibil_check", "loan")]
    selected = [_Def(1, "run_cibil_check", "loan")]  # same id
    result = build_workspace_match_result(actions, [], selected_actions=selected)
    assert result.action_names == ["run_cibil_check"]
    assert len(result.matched_actions) == 1


def test_duplicate_workspace_actions_are_deduplicated_by_id():
    actions = [_Def(1, "run_cibil_check", "loan"), _Def(1, "run_cibil_check", "loan")]
    result = build_workspace_match_result(actions, [])
    assert len(result.matched_actions) == 1


def test_empty_workspace_yields_empty_result():
    result = build_workspace_match_result([], [])
    assert result.action_names == []
    assert result.trigger_names == []
    assert result.workflow_type is None


# ── Critical invariant (requirement 17) ────────────────────────────────────────
#
# Workspace A has actions A, B, C. Global catalog also has D, E, F.
# Generating inside workspace A must expose ONLY A, B, C to the LLM — never
# D/E/F — unless the user explicitly selects them.

_A = _Def(1, "action_a", "loan")
_B = _Def(2, "action_b", "loan")
_C = _Def(3, "action_c", "loan")
_D = _Def(4, "action_d", "loan")
_E = _Def(5, "action_e", "loan")
_F = _Def(6, "action_f", "loan")


def test_global_only_actions_do_not_leak_into_workspace():
    workspace_actions = [_A, _B, _C]  # only what the workspace mapped
    result = build_workspace_match_result(workspace_actions, [])
    assert result.action_names == ["action_a", "action_b", "action_c"]
    # D, E, F are NOT available to the LLM automatically.
    assert "action_d" not in result.action_names
    assert "action_e" not in result.action_names
    assert "action_f" not in result.action_names


def test_explicitly_selected_global_action_is_added():
    workspace_actions = [_A, _B, _C]
    result = build_workspace_match_result(workspace_actions, [], selected_actions=[_E])
    assert set(result.action_names) == {"action_a", "action_b", "action_c", "action_e"}
    # Only the explicitly selected global leaked in — D and F still absent.
    assert "action_d" not in result.action_names
    assert "action_f" not in result.action_names
