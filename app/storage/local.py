"""
app/storage/local.py

LocalStorageProvider — stores files on the local filesystem.

Keys are treated as paths relative to a configured base directory. Parent
directories are created on write. This is the only provider needed for the
MVP; cloud providers implement the same StorageProvider contract later.
"""

from pathlib import Path

from app.core.setting import FILE_STORAGE_PATH
from app.storage.base import StorageProvider
from app.storage.exceptions import (
    FileNotFoundInStorageError,
    StorageWriteError,
)


class LocalStorageProvider(StorageProvider):
    """Filesystem-backed storage under a single base directory."""

    provider_name = "local"

    def __init__(self, base_path: Path | str = FILE_STORAGE_PATH):
        # No filesystem side effects at construction time — the base directory
        # is created lazily on the first write (see save()). This keeps merely
        # importing/instantiating the provider free of disk I/O.
        self._base_path = Path(base_path)

    def _resolve(self, key: str) -> Path:
        """Resolve ``key`` to an absolute path, guarding against traversal."""
        target = (self._base_path / key).resolve()
        base = self._base_path.resolve()
        # Prevent keys like "../../etc/passwd" from escaping the base dir.
        if base != target and base not in target.parents:
            raise StorageWriteError(f"Invalid storage key (path traversal): {key}")
        return target

    def save(self, key: str, content: bytes) -> None:
        path = self._resolve(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        except OSError as exc:
            raise StorageWriteError(
                f"Failed to write file to '{path}': {exc}"
            ) from exc

    def load(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundInStorageError(key)
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()
