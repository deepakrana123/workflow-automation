"""Unit tests for the file storage layer.

Covers LocalStorageProvider (byte IO, traversal guard) and FileStorageService
(store/retrieve, workspace-scoped keys, StoredFile metadata).
"""

import pytest

from app.execution.python.base.generate_model import GeneratedFile
from app.execution.python.base.stored import StoredFile
from app.storage.exceptions import (
    FileNotFoundInStorageError,
    StorageWriteError,
)
from app.storage.local import LocalStorageProvider
from app.storage.service import FileStorageService


@pytest.fixture
def provider(tmp_path):
    return LocalStorageProvider(base_path=tmp_path)


@pytest.fixture
def service(provider):
    return FileStorageService(provider)


def _generated(name="document.pdf") -> GeneratedFile:
    return GeneratedFile(
        file_name=name,
        mime_type="application/pdf",
        content=b"%PDF-1.4 hello",
        extension="pdf",
        size=len(b"%PDF-1.4 hello"),
    )


# ── LocalStorageProvider ──────────────────────────────────────────────────────

def test_save_then_load_round_trips(provider):
    provider.save("a/b.txt", b"hello")
    assert provider.load("a/b.txt") == b"hello"


def test_exists_reflects_state(provider):
    assert provider.exists("x.txt") is False
    provider.save("x.txt", b"data")
    assert provider.exists("x.txt") is True


def test_delete_removes_file(provider):
    provider.save("x.txt", b"data")
    provider.delete("x.txt")
    assert provider.exists("x.txt") is False


def test_delete_missing_is_noop(provider):
    provider.delete("never.txt")  # must not raise


def test_load_missing_raises(provider):
    with pytest.raises(FileNotFoundInStorageError):
        provider.load("missing.txt")


def test_path_traversal_is_blocked(provider):
    with pytest.raises(StorageWriteError):
        provider.save("../escape.txt", b"nope")


def test_provider_name_is_local(provider):
    assert provider.provider_name == "local"


# ── FileStorageService ────────────────────────────────────────────────────────

def test_store_returns_stored_file(service):
    stored = service.store(_generated(), workspace_id=7)
    assert isinstance(stored, StoredFile)
    assert stored.storage_provider == "local"
    assert stored.file_name == "document.pdf"
    assert stored.file_id


def test_store_scopes_key_by_workspace(service):
    stored = service.store(_generated(), workspace_id=7)
    assert stored.storage_path.startswith("7/")


def test_store_without_workspace_uses_global_scope(service):
    stored = service.store(_generated())
    assert stored.storage_path.startswith("global/")


def test_stored_file_is_retrievable(service):
    stored = service.store(_generated(), workspace_id=1)
    assert service.retrieve(stored.storage_path) == b"%PDF-1.4 hello"


def test_two_stores_get_distinct_ids(service):
    a = service.store(_generated(), workspace_id=1)
    b = service.store(_generated(), workspace_id=1)
    assert a.file_id != b.file_id
    assert a.storage_path != b.storage_path
