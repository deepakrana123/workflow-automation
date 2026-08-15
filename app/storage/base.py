"""
app/storage/base.py

StorageProvider — the abstraction every storage backend implements.

A provider is a *dumb byte store* keyed by an opaque string ("key"). It knows
nothing about workspaces, file ids, or MIME types; that policy lives in
FileStorageService. This keeps providers small and interchangeable
(local disk today; S3/Azure/GCS later) with zero changes at the call sites.
"""

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Contract for a byte-oriented storage backend."""

    #: Short identifier recorded on StoredFile (e.g. "local", "s3").
    provider_name: str = "abstract"

    @abstractmethod
    def save(self, key: str, content: bytes) -> None:
        """Persist ``content`` under ``key`` (overwriting any existing value)."""

    @abstractmethod
    def load(self, key: str) -> bytes:
        """Return the bytes stored at ``key``.

        Raises:
            FileNotFoundInStorageError: If ``key`` does not exist.
        """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return ``True`` if ``key`` exists in the store."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove ``key`` from the store. A no-op if it does not exist."""
