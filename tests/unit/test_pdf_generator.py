"""Unit tests for the PDF generation layer.

Covers PDFGeneratorService (generation, validation, file-name normalisation)
and GeneratePDFHandler (ActionResult adaptation).
"""

import pytest

from app.execution.python.base.exceptions import EmptyPayloadError
from app.execution.python.base.generate_model import GeneratedFile
from app.execution.python.pdf.generator import PDFGeneratorService
from app.execution.python.pdf.handler import GeneratePDFHandler
from app.workflow_execution.schemas.action_result import ActionResult


@pytest.fixture
def payload() -> dict:
    return {
        "customer_name": "Asha Rao",
        "loan_number": "LN-2024-0001",
        "branch": "Bengaluru MG Road",
    }


@pytest.fixture
def storage(tmp_path):
    """A FileStorageService backed by an isolated temp directory."""
    from app.storage.local import LocalStorageProvider
    from app.storage.service import FileStorageService

    return FileStorageService(LocalStorageProvider(base_path=tmp_path))


# ── PDFGeneratorService ───────────────────────────────────────────────────────

def test_generate_succeeds(payload):
    result = PDFGeneratorService().generate(payload, {})
    assert isinstance(result, GeneratedFile)


def test_file_name_defaults_to_document_pdf(payload):
    result = PDFGeneratorService().generate(payload, {})
    assert result.file_name == "document.pdf"


def test_file_name_uses_configured_output_name(payload):
    result = PDFGeneratorService().generate(
        payload, {"output_name": "loan_statement.pdf"}
    )
    assert result.file_name == "loan_statement.pdf"


def test_pdf_extension_is_appended_when_missing(payload):
    result = PDFGeneratorService().generate(
        payload, {"output_name": "loan_statement"}
    )
    assert result.file_name == "loan_statement.pdf"


def test_mime_type_is_pdf(payload):
    result = PDFGeneratorService().generate(payload, {})
    assert result.mime_type == "application/pdf"
    assert result.extension == "pdf"


def test_content_length_is_positive(payload):
    result = PDFGeneratorService().generate(payload, {})
    assert result.size > 0
    assert result.size == len(result.content)


def test_content_starts_with_pdf_magic_bytes(payload):
    """The most reliable sanity check: real PDFs begin with %PDF."""
    result = PDFGeneratorService().generate(payload, {})
    assert result.content.startswith(b"%PDF")


def test_empty_payload_is_rejected():
    with pytest.raises(EmptyPayloadError):
        PDFGeneratorService().generate({}, {})


def test_missing_values_are_handled_gracefully():
    # Only one field present; others must fall back without raising.
    result = PDFGeneratorService().generate({"customer_name": "Asha"}, {})
    assert result.content.startswith(b"%PDF")


# ── GeneratePDFHandler ────────────────────────────────────────────────────────

def test_handler_returns_successful_action_result(payload, storage):
    result = GeneratePDFHandler(storage=storage)(payload, {"output_name": "statement"})
    assert isinstance(result, ActionResult)
    assert result.success is True
    assert result.outputs["file_name"] == "statement.pdf"
    assert result.outputs["mime_type"] == "application/pdf"
    assert result.outputs["size"] > 0
    assert result.outputs["storage_provider"] == "local"
    assert result.outputs["file_id"]


def test_handler_stores_a_retrievable_pdf(payload, storage):
    result = GeneratePDFHandler(storage=storage)(payload, {})
    content = storage.retrieve(result.outputs["storage_path"])
    assert content.startswith(b"%PDF")


def test_handler_empty_payload_returns_failure(storage):
    result = GeneratePDFHandler(storage=storage)({}, {})
    assert result.success is False
    assert result.error is not None
