import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.knowledge_ingestions.service import KnowledgeIngestionService
from app.knowledge_ingestions.exceptions import (
    DocumentExtractionError,
    WorkflowExtractionError,
    RepositoryError,
)
from app.models.workspace import Workspace
from app.core.logger import logger

router = APIRouter(prefix="/knowledge-ingestion", tags=["knowledge-ingestion"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}


def _ingest_one(
    service: KnowledgeIngestionService,
    file: UploadFile,
    workspace_id: int,
) -> dict:
    """Ingest a single BRD, returning a per-file result (never raises).

    Isolating each file means one bad document does not abort the batch.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return {
            "filename": file.filename,
            "status": "failed",
            "error": f"Invalid file type '{file.content_type}'. Only PDF is accepted.",
        }

    content = file.file.read()
    if not content:
        return {
            "filename": file.filename,
            "status": "failed",
            "error": "Uploaded file is empty.",
        }

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        knowledge = service.ingest(
            tmp_path,
            workspace_id=workspace_id,
            source_document=file.filename,
        )
        logger.info(
            "knowledge_ingestion_success",
            extra={"extra_data": {
                "workflow_id": knowledge.id,
                "workflow_name": knowledge.workflow_name,
                "filename": file.filename,
                "workspace_id": workspace_id,
            }},
        )
        return {
            "filename": file.filename,
            "status": "success",
            "workflow_id": knowledge.id,
            "workflow_name": knowledge.workflow_name,
        }

    except (DocumentExtractionError, WorkflowExtractionError, RepositoryError) as exc:
        logger.warning(
            "knowledge_ingestion_failed",
            extra={"extra_data": {
                "error": str(exc),
                "filename": file.filename,
                "error_type": type(exc).__name__,
            }},
        )
        return {"filename": file.filename, "status": "failed", "error": str(exc)}

    except Exception as exc:  # noqa: BLE001 - reported per file, batch continues
        logger.error(
            "knowledge_ingestion_unexpected_error",
            extra={"extra_data": {"error": str(exc), "filename": file.filename}},
        )
        return {
            "filename": file.filename,
            "status": "failed",
            "error": "Ingestion failed unexpectedly.",
        }

    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


@router.post("/upload")
def upload_brds(
    files: list[UploadFile] = File(...),
    workspace_id: int = Form(1),
    db: Session = Depends(get_db),
):
    """Ingest one or more BRD PDFs into a workspace.

    Each file is ingested independently — partial success is reported per file.
    Every BRD becomes its own WorkflowKnowledge tagged with its source filename,
    all owned by the given workspace.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.active.is_(True))
        .first()
    )
    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Active workspace {workspace_id} not found.",
        )

    service = KnowledgeIngestionService(db=db)
    results = [_ingest_one(service, f, workspace_id) for f in files]

    succeeded = sum(1 for r in results if r["status"] == "success")
    return {
        "workspace_id": workspace_id,
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": results,
    }
