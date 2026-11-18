"""
app/core/setting.py

Runtime path configuration for external OCR dependencies.

Override with environment variables in production / Docker:
  TESSERACT_PATH   — full path to the tesseract executable
  POPPLER_PATH     — path to the Poppler bin directory

Defaults point to:
  - Linux / Docker: standard install locations (/usr/bin, /usr/bin/tesseract)
  - Windows: attempts to detect from Conda/Chocolatey or system PATH
  - macOS: standard Homebrew location
"""

import os
import sys
from pathlib import Path


def _detect_poppler_path() -> Path | None:
    """
    Detect Poppler installation on Windows, macOS, or Linux.
    
    Detection order:
      1. POPPLER_PATH environment variable (user override)
      2. Windows Conda environment: <env>/Library/bin
      3. Windows Chocolatey: C:\\Program Files\\poppler\\Library\\bin
      4. macOS Homebrew: /usr/local/opt/poppler/bin or /opt/homebrew/opt/poppler/bin
      5. Linux standard: /usr/bin
      6. System PATH: pdftoppm command
    """
    # User override takes precedence
    if env_path := os.getenv("POPPLER_PATH"):
        return Path(env_path)
    
    # Windows detection
    if sys.platform == "win32":
        # Try Conda environment first (most common for data scientists)
        if conda_prefix := os.getenv("CONDA_PREFIX"):
            conda_path = Path(conda_prefix) / "Library" / "bin"
            if (conda_path / "pdftoppm.exe").exists():
                return conda_path
        
        # Try Chocolatey installation
        choco_path = Path("C:\\Program Files\\poppler\\Library\\bin")
        if (choco_path / "pdftoppm.exe").exists():
            return choco_path
    
    # macOS detection (Homebrew)
    elif sys.platform == "darwin":
        homebrew_paths = [
            Path("/usr/local/opt/poppler/bin"),      # Intel Macs
            Path("/opt/homebrew/opt/poppler/bin"),   # Apple Silicon
        ]
        for hb_path in homebrew_paths:
            if (hb_path / "pdftoppm").exists():
                return hb_path
    
    # Linux or fallback to standard location
    linux_path = Path("/usr/bin")
    if (linux_path / "pdftoppm").exists():
        return linux_path
    
    # Last resort: assume it's in system PATH and let pdf2image find it
    return None


TESSERACT_PATH = Path(
    os.getenv("TESSERACT_PATH", "/usr/bin/tesseract")
)

POPPLER_PATH = _detect_poppler_path() or Path(
    os.getenv("POPPLER_PATH", "/usr/bin")
)

# Base directory for the local file storage provider. Generated files
# (PDF/CSV/Excel) and other workspace artifacts are written under here.
# Override with FILE_STORAGE_PATH in production / Docker (e.g. a mounted volume).
FILE_STORAGE_PATH = Path(
    os.getenv("FILE_STORAGE_PATH", "/data/mflows/files")
)
