from io import BytesIO

from openpyxl import Workbook

from app.execution.python.base.exceptions import (
    EmptyPayloadError,
    InvalidConfigurationError,
)
from app.execution.python.base.file_generator import FileGenerator
from app.execution.python.base.generate_model import GeneratedFile

# Official MIME type for .xlsx (OpenXML spreadsheet) files.
XLSX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


class ExcelGeneratorService(FileGenerator):
    """Generate Excel (.xlsx) files from a payload using openpyxl.

    This service implements the :class:`FileGenerator` contract. It turns a
    payload into a worksheet (a header row plus one row per record), renders
    that workbook into ``.xlsx`` bytes, and wraps the result in a
    :class:`GeneratedFile`.
    """

    def generate(self, payload: dict, configuration: dict) -> GeneratedFile:
        """Build an Excel file from the given payload.

        Args:
            payload: The data used to populate the spreadsheet.
            configuration: Generation options such as the output file name.

        Returns:
            The generated workbook wrapped in a :class:`GeneratedFile`.

        Raises:
            EmptyPayloadError: If ``payload`` is empty or falsy.
        """
        if not payload:
            raise EmptyPayloadError(self.__class__.__name__)

        rows = self._build_rows(payload, configuration)
        content = self._build_workbook(rows, configuration)
        return self._create_generated_file(content, configuration)

    def _build_rows(self, payload: dict, configuration: dict) -> list:
        """Build the list of rows for the worksheet.

        Renders a header row followed by one row per record. Missing values
        fall back to ``""`` so the sheet is always well formed.

        Args:
            payload: The data used to populate the spreadsheet.
            configuration: Generation options that influence the layout.

        Returns:
            A list of rows (the first being the header row).

        Raises:
            InvalidConfigurationError: If ``headers`` are not provided.
        """
        if isinstance(payload, dict):
            payload = [payload]

        headers = configuration.get("headers")
        if not headers:
            raise InvalidConfigurationError("Excel headers are required.")

        rows = [headers]
        for record in payload:
            row = [record.get(header, "") for header in headers]
            rows.append(row)

        return rows

    def _build_workbook(self, rows: list, configuration: dict) -> bytes:
        """Render a list of rows into ``.xlsx`` bytes.

        Args:
            rows: The list of rows to write (header row first).
            configuration: Generation options; ``sheet_name`` sets the
                worksheet title and defaults to ``"Sheet1"``.

        Returns:
            The rendered workbook as raw ``.xlsx`` bytes.
        """
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = configuration.get("sheet_name", "Sheet1")

        for row in rows:
            worksheet.append(row)

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def _create_generated_file(
        self, content: bytes, configuration: dict
    ) -> GeneratedFile:
        """Wrap raw ``.xlsx`` bytes in a :class:`GeneratedFile`.

        Args:
            content: The rendered workbook as raw bytes.
            configuration: Generation options; ``output_name`` sets the file
                name and defaults to ``"document.xlsx"``.

        Returns:
            The workbook bytes wrapped with file metadata.
        """
        file_name = self._normalise_file_name(
            configuration.get("output_name", "document.xlsx")
        )

        return GeneratedFile(
            file_name=file_name,
            mime_type=XLSX_MIME_TYPE,
            extension="xlsx",
            content=content,
            size=len(content),
        )

    @staticmethod
    def _normalise_file_name(output_name: str) -> str:
        """Ensure the output file name ends with a ``.xlsx`` extension.

        Args:
            output_name: The requested file name from the configuration.

        Returns:
            The file name guaranteed to end with ``.xlsx`` (case-insensitive
            match; the extension is appended when missing).
        """
        name = (output_name or "document.xlsx").strip()
        if not name.lower().endswith(".xlsx"):
            name = f"{name}.xlsx"
        return name
