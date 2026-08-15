from dataclasses import dataclass

from app.execution.python.base.generate_model import GeneratedFile


@dataclass(slots=True)
class StoredFile:
    file_id: str
    file_name: str
    storage_provider: str
    storage_path: str
    public_url: str | None
    generated_file: GeneratedFile
