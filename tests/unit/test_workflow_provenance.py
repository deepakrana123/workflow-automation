"""Unit tests for the deterministic workflow provenance builder (pure)."""

from app.workflow.workflow_provenance import build_provenance, SOURCE_BRD, SOURCE_GENERATED


_STEPS = [
    {"id": "a", "action": "run_cibil_check"},
    {"id": "b", "action": "approve_loan"},
    {"id": "c", "action": "notify_customer"},
]

_MAPPINGS = {
    "run_cibil_check": {
        "term": "credit bureau check",
        "clause": "The system shall verify the applicant's CIBIL score.",
        "confidence": 0.9,
        "similarity": 0.82,
        "status": "MAPPED",
    },
    "approve_loan": {
        "term": "approve the loan",
        "clause": "Approve if score exceeds 750.",
        "confidence": 0.7,
        "similarity": 0.6,
        "status": "MAPPED",
    },
}


def test_brd_step_carries_source_and_confidence():
    prov = build_provenance(1, _STEPS, _MAPPINGS, raw_input="req", source_document="brd.pdf")
    a = next(s for s in prov["steps"] if s["id"] == "a")
    assert a["source_type"] == SOURCE_BRD
    assert a["source_term"] == "credit bureau check"
    assert "CIBIL" in a["source_clause"]
    assert a["confidence"] == 0.9


def test_unmapped_step_falls_back_to_generated():
    prov = build_provenance(1, _STEPS, _MAPPINGS, raw_input="the NL request", source_document="brd.pdf")
    c = next(s for s in prov["steps"] if s["id"] == "c")
    assert c["source_type"] == SOURCE_GENERATED
    assert c["source_clause"] == "the NL request"
    assert c["confidence"] is None


def test_grounded_flag_true_when_any_brd_mapping():
    prov = build_provenance(1, _STEPS, _MAPPINGS, raw_input="r", source_document="brd.pdf")
    assert prov["grounded"] is True


def test_grounded_flag_false_when_no_mappings():
    prov = build_provenance(1, _STEPS, {}, raw_input="r", source_document=None)
    assert prov["grounded"] is False
    assert all(s["source_type"] == SOURCE_GENERATED for s in prov["steps"])


def test_average_confidence_only_over_mapped_steps():
    prov = build_provenance(1, _STEPS, _MAPPINGS, raw_input="r", source_document="brd.pdf")
    # (0.9 + 0.7) / 2 = 0.8
    assert prov["average_confidence"] == 0.8


def test_average_confidence_none_when_no_confidences():
    prov = build_provenance(1, _STEPS, {}, raw_input="r", source_document=None)
    assert prov["average_confidence"] is None


def test_source_document_passthrough():
    prov = build_provenance(1, _STEPS, _MAPPINGS, raw_input="r", source_document="loan_brd.pdf")
    assert prov["source_document"] == "loan_brd.pdf"
    assert prov["workflow_id"] == 1
