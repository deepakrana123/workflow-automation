"""
app/core/setting.py

Runtime path configuration for external OCR dependencies.

Override with environment variables in production / Docker:
  TESSERACT_PATH   — full path to the tesseract executable
  POPPLER_PATH     — path to the Poppler bin directory

Defaults point to standard Linux install locations (used in containers).
The Windows developer paths are no longer hardcoded here.
"""

import os
from pathlib import Path

TESSERACT_PATH = Path(
    os.getenv("TESSERACT_PATH", "/usr/bin/tesseract")
)

POPPLER_PATH = Path(
    os.getenv("POPPLER_PATH", "/usr/bin")
)

# Base directory for the local file storage provider. Generated files
# (PDF/CSV/Excel) and other workspace artifacts are written under here.
# Override with FILE_STORAGE_PATH in production / Docker (e.g. a mounted volume).
FILE_STORAGE_PATH = Path(
    os.getenv("FILE_STORAGE_PATH", "/data/mflows/files")
)
