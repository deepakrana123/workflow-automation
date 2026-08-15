"""Unit tests for the CSV generation layer.

Covers CSVGeneratorService (generation, validation, file-name normalisation)
and GenerateCSVHandler (ActionResult adaptation).
"""

import csv
import io

import pytest

from app.execution.python.base.exceptions import (
    EmptyPayloadError,
    InvalidConfigurationError,
)
from app.execution.python.base.generate_model import GeneratedFile
from app.execution.python.csv.generator import CSVGeneratorService
from app.execution.python.csv.handler import GenerateCSVHandler
from app.workflow_execution.schemas.action_result import ActionResult


@pytest.fixture
def payload() -> dict:
    return {
        "customer_name": "Asha Rao",
        "loan_number": "LN-2024-0001",
        "branch": "Bengaluru MG Road",
    }


@pytest.fixture
def config() -> dict:
    return {"headers": ["customer_name", "loan_number", "branch"]}


@pytest.fixture
def storage(tmp_path):
    """A FileStorageService backed by an isolated temp directory."""
    from app.storage.local import LocalStorageProvider
    from app.storage.service import FileStorageService

    return FileStorageService(LocalStorageProvider(base_path=tmp_path))


def _read_rows(content: bytes) -> list[list[str]]:
    """Decode CSV bytes back into rows for assertions."""
    text = content.decode("utf-8")
    return list(csv.reader(io.StringIO(text)))


# ── CSVGeneratorService ───────────────────────────────────────────────────────

def test_generate_succeeds(payload, config):
    result = CSVGeneratorService().generate(payload, config)
    assert isinstance(result, GeneratedFile)


def test_file_name_defaults_to_document_csv(payload, config):
    result = CSVGeneratorService().generate(payload, config)
    assert result.file_name == "document.csv"


def test_file_name_uses_configured_output_name(payload, config):
    result = CSVGeneratorService().generate(
        payload, {**config, "output_name": "loan_export.csv"}
    )
    assert result.file_name == "loan_export.csv"


def test_csv_extension_is_appended_when_missing(payload, config):
    result = CSVGeneratorService().generate(
        payload, {**config, "output_name": "loan_export"}
    )
    assert result.file_name == "loan_export.csv"


def test_mime_type_is_csv(payload, config):
    result = CSVGeneratorService().generate(payload, config)
    assert result.mime_type == "text/csv"
    assert result.extension == "csv"


def test_content_length_is_positive(payload, config):
    result = CSVGeneratorService().generate(payload, config)
    assert result.size > 0
    assert result.size == len(result.content)


def test_header_row_and_data_row_are_written(payload, config):
    result = CSVGeneratorService().generate(payload, config)
    rows = _read_rows(result.content)
    assert rows[0] == ["customer_name", "loan_number", "branch"]
    assert rows[1] == ["Asha Rao", "LN-2024-0001", "Bengaluru MG Road"]


def test_missing_values_fall_back_to_empty_string(config):
    result = CSVGeneratorService().generate({"customer_name": "Asha"}, config)
    rows = _read_rows(result.content)
    # loan_number and branch are absent -> empty strings, no exception.
    assert rows[1] == ["Asha", "", ""]


def test_dict_payload_is_wrapped_into_a_single_row(payload, config):
    result = CSVGeneratorService().generate(payload, config)
    rows = _read_rows(result.content)
    assert len(rows) == 2  # header + one record


def test_empty_payload_is_rejected(config):
    with pytest.raises(EmptyPayloadError):
        CSVGeneratorService().generate({}, config)


def test_missing_headers_are_rejected(payload):
    with pytest.raises(InvalidConfigurationError):
        CSVGeneratorService().generate(payload, {})


# ── GenerateCSVHandler ────────────────────────────────────────────────────────

def test_handler_returns_successful_action_result(payload, config, storage):
    result = GenerateCSVHandler(storage=storage)(
        payload, {**config, "output_name": "export"}
    )
    assert isinstance(result, ActionResult)
    assert result.success is True
    assert result.outputs["file_name"] == "export.csv"
    assert result.outputs["mime_type"] == "text/csv"
    assert result.outputs["size"] > 0
    assert result.outputs["storage_provider"] == "local"
    assert result.outputs["file_id"]


def test_handler_stores_a_retrievable_csv(payload, config, storage):
    result = GenerateCSVHandler(storage=storage)(payload, config)
    content = storage.retrieve(result.outputs["storage_path"])
    rows = _read_rows(content)
    assert rows[0] == ["customer_name", "loan_number", "branch"]


def test_handler_empty_payload_returns_failure(config, storage):
    result = GenerateCSVHandler(storage=storage)({}, config)
    assert result.success is False
    assert result.error is not None


def test_handler_missing_headers_returns_failure(payload, storage):
    result = GenerateCSVHandler(storage=storage)(payload, {})
    assert result.success is False
    assert result.error is not None
