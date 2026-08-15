"""
app/storage/exceptions.py

Exception hierarchy for the file storage layer.
"""


class StorageError(Exception):
    """Base class for all storage errors."""


class FileNotFoundInStorageError(StorageError):
    """Raised when a requested storage key does not exist."""

    def __init__(self, storage_path: str):
        super().__init__(f"No file found at storage path: {storage_path}")
        self.storage_path = storage_path


class StorageWriteError(StorageError):
    """Raised when writing a file to the backing store fails."""
