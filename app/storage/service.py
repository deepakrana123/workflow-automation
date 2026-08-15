"""
app/storage/service.py

FileStorageService — the policy layer over a StorageProvider.

Responsibilities the provider deliberately does NOT have:
  - generating a unique file id
  - deciding the storage key layout (workspace-scoped)
  - wrapping the result in a StoredFile with metadata

Callers depend on this service, not on a concrete provider, so the backing
store can change without touching them.
"""

import uuid
from pathlib import PurePosixPath

from app.execution.python.base.generate_model import GeneratedFile
from app.execution.python.base.stored import StoredFile
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider


class FileStorageService:
    """Store and retrieve files through a pluggable StorageProvider."""

    def __init__(self, provider: StorageProvider | None = None):
        """Create the service.

        Args:
            provider: The storage backend. Defaults to
                :class:`LocalStorageProvider`, which also makes the service
                easy to unit test with a fake provider.
        """
        self._provider = provider or LocalStorageProvider()

    def store(
        self,
        generated: GeneratedFile,
        *,
        workspace_id: int | None = None,
    ) -> StoredFile:
        """Persist a generated file and return its :class:`StoredFile`.

        The storage key is workspace-scoped so files never collide across
        workspaces: ``{workspace}/{file_id}_{file_name}``.

        Args:
            generated: The in-memory file to persist.
            workspace_id: Owning workspace; ``None`` falls back to ``"global"``.

        Returns:
            Metadata describing where the file was stored.
        """
        file_id = uuid.uuid4().hex
        scope = str(workspace_id) if workspace_id is not None else "global"
        # PurePosixPath keeps keys forward-slashed regardless of host OS.
        key = str(PurePosixPath(scope) / f"{file_id}_{generated.file_name}")

        self._provider.save(key, generated.content)

        return StoredFile(
            file_id=file_id,
            file_name=generated.file_name,
            storage_provider=self._provider.provider_name,
            storage_path=key,
            public_url=None,
            generated_file=generated,
        )

    def retrieve(self, storage_path: str) -> bytes:
        """Return the raw bytes stored at ``storage_path``.

        Raises:
            FileNotFoundInStorageError: If the path does not exist.
        """
        return self._provider.load(storage_path)
