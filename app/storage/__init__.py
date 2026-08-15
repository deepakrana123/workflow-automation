"""
app/storage

File storage layer for MFlows.

A generated or uploaded file flows through:

    GeneratedFile (bytes)
        -> FileStorageService.store()
        -> StorageProvider.save()          (LocalStorageProvider for now)
        -> StoredFile (metadata + storage_path)

Retrieval is the reverse: FileStorageService.retrieve(storage_path) -> bytes.

The StorageProvider abstraction keeps the call sites unaware of *where* files
live, so S3/Azure/GCS providers can be added later without touching callers.
"""

from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider
from app.storage.service import FileStorageService

__all__ = [
    "StorageProvider",
    "LocalStorageProvider",
    "FileStorageService",
]
