import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.knowledge_ingestions.service import KnowledgeIngestionService
from app.knowledge_ingestions.exceptions import (
    DocumentExtractionError,
    WorkflowExtractionError,
    RepositoryError,
)
from app.core.logger import logger

router = APIRouter(prefix="/knowledge-ingestion", tags=["knowledge-ingestion"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post("/upload")
def upload_brd(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Accept a BRD PDF, extract workflow knowledge, persist to DB,
    run embedding-based mapping, and return the ingestion result.
    """
    # ── Validate content type ─────────────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only PDF is accepted.",
        )

    # ── Validate non-empty ────────────────────────────────────────────────────
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # ── Write to temp file, pass path to service ─────────────────────────────
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        service = KnowledgeIngestionService(db=db)
        knowledge = service.ingest(tmp_path)

        logger.info(
            "knowledge_ingestion_success",
            extra={
                "extra_data": {
                    "workflow_id": knowledge.id,
                    "workflow_name": knowledge.workflow_name,
                    "filename": file.filename,
                }
            },
        )

        return {
            "workflow_id": knowledge.id,
            "workflow_name": knowledge.workflow_name,
            "status": "success",
        }

    except HTTPException:
        raise

    except DocumentExtractionError as e:
        logger.warning(
            "knowledge_ingestion_extraction_failed",
            extra={"extra_data": {"error": str(e), "filename": file.filename}},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except WorkflowExtractionError as e:
        logger.warning(
            "knowledge_ingestion_workflow_extraction_failed",
            extra={"extra_data": {"error": str(e), "filename": file.filename}},
        )
        raise HTTPException(status_code=500, detail=str(e))

    except RepositoryError as e:
        logger.error(
            "knowledge_ingestion_repository_failed",
            extra={"extra_data": {"error": str(e), "filename": file.filename}},
        )
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(
            "knowledge_ingestion_unexpected_error",
            extra={"extra_data": {"error": str(e), "filename": file.filename}},
        )
        raise HTTPException(status_code=500, detail="Ingestion failed unexpectedly.")

    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()
