"""
Phase 2.4 — Natural Language Pipeline Tests

Tests:
    1.  Valid single-action sentence
    2.  Valid multi-action sentence (then-separated)
    3.  Valid multi-action sentence (and-separated)
    4.  Multiple actions produce sequential depends_on chain
    5.  Unknown trigger raises UnknownTriggerError
    6.  Unknown action raises UnknownActionError
    7.  Empty sentence raises ValueError
    8.  AST validator accepts NL-produced AST
    9.  WorkflowComplier produces v2-compatible output from NL
    10. Sentence without "when" keyword still extracts trigger
    11. Case-insensitive matching
    12. Single action produces step with no dependencies
"""

import pytest

from app.nlp.nl.nl_service import NLService
from app.nlp.nl.intent_extractor import (
    IntentExtractor,
    UnknownTriggerError,
    UnknownActionError,
)
from app.nlp.ast.validator import ASTValidator
from app.nlp.ast.execptions import ASTValidationError
from app.nlp.complier.workflow_complier import WorkflowComplier


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def service():
    return NLService()


@pytest.fixture
def extractor():
    return IntentExtractor()


@pytest.fixture
def compiler():
    return WorkflowComplier()


@pytest.fixture
def validator():
    return ASTValidator()


# ── 1. Valid single-action sentence ──────────────────────────────────────────

def test_valid_single_action(service):
    ast = service.parse("When payment is due send reminder")
    assert ast.trigger.event == "payment_due"
    assert len(ast.steps) == 1
    assert ast.steps[0].action == "send_reminder"


# ── 2. Valid multi-action sentence (then) ─────────────────────────────────────

def test_valid_multi_action_then(service):
    ast = service.parse(
        "When payment is due send reminder then notify manager then close case"
    )
    assert ast.trigger.event == "payment_due"
    assert len(ast.steps) == 3
    actions = [s.action for s in ast.steps]
    assert actions == ["send_reminder", "notify_manager", "close_case"]


# ── 3. Valid multi-action sentence (and) ──────────────────────────────────────

def test_valid_multi_action_and(service):
    ast = service.parse(
        "When ticket created create support ticket and assign support agent"
    )
    assert ast.trigger.event == "ticket_created"
    assert len(ast.steps) == 2
    assert ast.steps[0].action == "create_support_ticket"
    assert ast.steps[1].action == "assign_support_agent"


# ── 4. Sequential dependency chain ────────────────────────────────────────────

def test_sequential_depends_on_chain(service):
    ast = service.parse(
        "When payment is due send reminder then notify manager then close case"
    )
    assert ast.steps[0].depends_on == []
    assert ast.steps[1].depends_on == ["1"]
    assert ast.steps[2].depends_on == ["2"]


# ── 5. Unknown trigger raises ─────────────────────────────────────────────────

def test_unknown_trigger_raises(service):
    with pytest.raises(UnknownTriggerError):
        service.parse("When alien invasion send reminder")


# ── 6. Unknown action raises ──────────────────────────────────────────────────

def test_unknown_action_raises(service):
    with pytest.raises(UnknownActionError):
        service.parse("When payment is due teleport customer")


# ── 7. Empty sentence raises ──────────────────────────────────────────────────

def test_empty_sentence_raises(service):
    with pytest.raises(ValueError):
        service.parse("")


def test_whitespace_only_raises(service):
    with pytest.raises(ValueError):
        service.parse("   ")


# ── 8. AST validator accepts NL-produced AST ──────────────────────────────────

def test_ast_validator_accepts_nl_ast(service, validator):
    ast = service.parse(
        "When payment is due send reminder then notify manager"
    )
    assert validator.validate(ast) is True


# ── 9. Compiler produces v2-compatible output ─────────────────────────────────

def test_compiler_produces_v2_output(service, compiler):
    ast = service.parse(
        "When payment is due send reminder then notify manager then close case"
    )
    result = compiler.compile(ast)
    assert result["version"] == "v2"
    assert result["trigger"]["event_type"] == "payment_due"
    assert len(result["steps"]) == 3
    assert result["steps"][0] == {
        "id": "1",
        "action": "send_reminder",
        "depends_on": [],
        "config": {},
    }
    assert result["steps"][1] == {
        "id": "2",
        "action": "notify_manager",
        "depends_on": ["1"],
        "config": {},
    }


# ── 10. Sentence without "when" still works ───────────────────────────────────

def test_no_when_keyword(service):
    ast = service.parse("payment is due send reminder")
    assert ast.trigger.event == "payment_due"
    assert ast.steps[0].action == "send_reminder"


# ── 11. Case-insensitive matching ─────────────────────────────────────────────

def test_case_insensitive(service):
    ast = service.parse("WHEN PAYMENT IS DUE SEND REMINDER")
    assert ast.trigger.event == "payment_due"
    assert ast.steps[0].action == "send_reminder"


# ── 12. Single action — no dependencies ───────────────────────────────────────

def test_single_action_no_depends_on(service):
    ast = service.parse("When payment is due send reminder")
    assert ast.steps[0].depends_on == []
