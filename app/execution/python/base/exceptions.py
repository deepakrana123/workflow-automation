"""
app/execution/python/base/exceptions.py

Exception hierarchy for the file generation layer.

All errors raised while building files (PDF, CSV, Excel, ...) inherit from
:class:`FileGenerationError` so callers can catch the base class when needed.
"""


class FileGenerationError(Exception):
    """Base class for all file generation errors."""


class EmptyPayloadError(FileGenerationError):
    """Raised when a generator is asked to build a file from an empty payload."""

    def __init__(self, generator: str):
        super().__init__(
            f"{generator} received an empty payload; nothing to generate."
        )
        self.generator = generator


class InvalidConfigurationError(FileGenerationError):
    """Raised when a generator receives invalid or incomplete configuration."""
