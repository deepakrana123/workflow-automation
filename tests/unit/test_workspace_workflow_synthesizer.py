"""Unit tests for deterministic multi-BRD DAG synthesis (no DB, no LLM)."""

from app.workflow.workspace_workflow_synthesizer import (
    order_actions,
    pick_trigger,
    build_synthesis_workflow_json,
    build_synthesis_provenance,
    _build_compiler_service,
)


def _synthesis():
    return {
        "brd_count": 2,
        "actions": [
            {"action": "approve_loan", "display_name": "Approve Loan", "contributed_by": 1,
             "sources": [{"source_document": "brd2.pdf", "clause": "Approve."}]},
            {"action": "run_cibil_check", "display_name": "Run CIBIL", "contributed_by": 2,
             "sources": [{"source_document": "brd1.pdf", "clause": "Check CIBIL."},
                         {"source_document": "brd2.pdf", "clause": "Verify credit."}]},
        ],
        "triggers": [
            {"trigger": "loan_application_received", "sources": [{"source_document": "brd1.pdf"}]},
        ],
    }


def test_order_actions_consensus_first():
    # run_cibil_check contributed by 2 BRDs -> comes before approve_loan (1).
    assert order_actions(_synthesis()) == ["run_cibil_check", "approve_loan"]


def test_pick_trigger_slugified():
    assert pick_trigger(_synthesis()) == "loan_application_received"


def test_pick_trigger_default_when_none():
    assert pick_trigger({"triggers": []}) == "workspace_workflow_triggered"


def test_build_workflow_json_sequential_dependencies():
    wf = build_synthesis_workflow_json(_synthesis(), "loan_application_received")
    actions = wf["workflow"]["actions"]
    assert actions[0] == {"name": "run_cibil_check", "dependencies": []}
    assert actions[1] == {"name": "approve_loan", "dependencies": ["run_cibil_check"]}
    assert wf["workflow"]["triggers"][0]["name"] == "loan_application_received"


def test_synthesis_compiles_to_sequential_dag():
    """The deterministic compile chain (no LLM) produces a valid linear DAG."""
    wf_json = build_synthesis_workflow_json(_synthesis(), "loan_application_received")
    result = _build_compiler_service().compile("finance", wf_json)
    compiled = result["compiled"]

    steps = compiled["steps"]
    assert [s["action"] for s in steps] == ["run_cibil_check", "approve_loan"]
    # Second step depends on the first (sequential chain).
    assert steps[0]["depends_on"] == []
    assert steps[1]["depends_on"] == [steps[0]["id"]]
    assert compiled["trigger"]["event_type"] == "loan_application_received"


def test_provenance_maps_steps_to_sources():
    wf_json = build_synthesis_workflow_json(_synthesis(), "t")
    compiled = _build_compiler_service().compile("finance", wf_json)["compiled"]
    prov = build_synthesis_provenance(compiled, _synthesis())

    cibil = next(p for p in prov if p["action"] == "run_cibil_check")
    assert len(cibil["sources"]) == 2  # contributed by 2 BRDs
    approve = next(p for p in prov if p["action"] == "approve_loan")
    assert approve["sources"][0]["source_document"] == "brd2.pdf"


def test_trigger_name_with_spaces_is_slugified():
    wf = build_synthesis_workflow_json(_synthesis(), "Loan Application Received")
    assert wf["workflow"]["triggers"][0]["name"] == "Loan_Application_Received"
