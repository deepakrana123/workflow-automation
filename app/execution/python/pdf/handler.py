"""
app/execution/python/pdf/handler.py

GeneratePDFHandler — action handler that produces a PDF file.

Flow:
    GeneratePDFHandler(payload, config)
        ↓
    PDFGeneratorService.generate(payload, config)  →  GeneratedFile
        ↓
    ActionResult

The handler adapts the file generation layer to the standard action contract
so PythonExecutor can invoke it like any other registered handler.
"""

from app.core.logger import logger
from app.execution.python.base.exceptions import FileGenerationError
from app.execution.python.pdf.generator import PDFGeneratorService
from app.storage.service import FileStorageService
from app.workflow_execution.schemas.action_result import ActionResult


class GeneratePDFHandler:
    """Generate a PDF, store it, and return an :class:`ActionResult`.

    The file is persisted through :class:`FileStorageService`; the result
    carries the storage reference (``file_id``/``storage_path``) rather than
    the raw bytes, so the workflow context stays small and the file is
    downloadable from the workspace.
    """

    def __init__(
        self,
        service: PDFGeneratorService | None = None,
        storage: FileStorageService | None = None,
    ):
        """Create the handler.

        Args:
            service: The PDF generator. Defaults to
                :class:`PDFGeneratorService`; injectable for tests.
            storage: The file storage service. Defaults to
                :class:`FileStorageService`; injectable for tests.
        """
        self._service = service or PDFGeneratorService()
        self._storage = storage or FileStorageService()

    def __call__(self, payload: dict, config: dict) -> ActionResult:
        """Invoke the handler like a plain callable (registry entry point).

        Args:
            payload: The data used to populate the PDF.
            config: Generation options such as ``output_name`` and ``title``.

        Returns:
            An :class:`ActionResult` describing the generated file, or a
            failure result when generation fails.
        """
        try:
            generated = self._service.generate(payload, config)
            stored = self._storage.store(
                generated, workspace_id=config.get("workspace_id")
            )
        except FileGenerationError as exc:
            logger.warning(
                "pdf_generation_rejected",
                extra={"extra_data": {"error": str(exc)}},
            )
            return ActionResult(
                success=False,
                error=str(exc),
                message="PDF generation rejected.",
            )
        except Exception as exc:  # noqa: BLE001 - surfaced as a failed action
            logger.exception("pdf_generation_failed")
            return ActionResult(
                success=False,
                error=str(exc),
                message="PDF generation failed.",
            )

        logger.info(
            "pdf_generated",
            extra={"extra_data": {
                "file_id": stored.file_id,
                "file_name": stored.file_name,
                "storage_path": stored.storage_path,
                "size": generated.size,
            }},
        )

        return ActionResult(
            success=True,
            outputs={
                "file_id": stored.file_id,
                "file_name": stored.file_name,
                "mime_type": generated.mime_type,
                "extension": generated.extension,
                "size": generated.size,
                "storage_provider": stored.storage_provider,
                "storage_path": stored.storage_path,
            },
            message=f"Generated PDF '{stored.file_name}'.",
        )


# Module-level callable for ActionHandlerRegistry (handler(payload, config)).
generate_pdf = GeneratePDFHandler()
