import csv
from io import StringIO

from app.execution.python.base.exceptions import (
    EmptyPayloadError,
    InvalidConfigurationError,
)
from app.execution.python.base.file_generator import FileGenerator
from app.execution.python.base.generate_model import GeneratedFile


class CSVGeneratorService(FileGenerator):
    """Generate CSV files from a payload.

    This service implements the :class:`FileGenerator` contract. It turns a
    payload into a list of rows, renders those rows into CSV bytes, and wraps
    the result in a :class:`GeneratedFile`.
    """

    def generate(self, payload: dict, configuration: dict) -> GeneratedFile:
        """Build a CSV file from the given payload.

        Args:
            payload: The data used to populate the CSV content.
            configuration: Generation options such as the output file name.

        Returns:
            The generated CSV wrapped in a :class:`GeneratedFile`.

        Raises:
            EmptyPayloadError: If ``payload`` is empty or falsy.
        """
        if not payload:
            raise EmptyPayloadError(self.__class__.__name__)

        rows = self._build_rows(payload, configuration)
        content = self._build_csv(rows)
        return self._create_generated_file(content, configuration)

    def _build_rows(self, payload: dict, configuration: dict) -> list:
        """Build the list of rows for the CSV document.

        Renders a header row followed by one row per record. Missing values
        fall back to ``""`` so the document is always well formed.

        Args:
            payload: The data used to populate the CSV content.
            configuration: Generation options that influence the layout.

        Returns:
            A list of rows to be written to the CSV document.

        Raises:
            InvalidConfigurationError: If ``headers`` are not provided.
        """
        if isinstance(payload, dict):
            payload = [payload]

        headers = configuration.get("headers")
        if not headers:
            raise InvalidConfigurationError("CSV headers are required.")

        rows = [headers]
        for record in payload:
            row = [record.get(header, "") for header in headers]
            rows.append(row)

        return rows

    def _build_csv(self, rows: list) -> bytes:
        """Render a list of rows into CSV bytes.

        Args:
            rows: The list of rows to render.

        Returns:
            The rendered CSV document as raw bytes.
        """
        buffer = StringIO()
        writer = csv.writer(
            buffer,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        for row in rows:
            writer.writerow(row)
        csv_content = buffer.getvalue()
        buffer.close()

        return csv_content.encode("utf-8")

    def _create_generated_file(
        self, content: bytes, configuration: dict
    ) -> GeneratedFile:
        """Wrap raw CSV bytes in a :class:`GeneratedFile`.

        Args:
            content: The rendered CSV document as raw bytes.
            configuration: Generation options; ``output_name`` sets the file
                name and defaults to ``"document.csv"``.

        Returns:
            The CSV bytes wrapped with file metadata.
        """
        file_name = self._normalise_file_name(
            configuration.get("output_name", "document.csv")
        )

        return GeneratedFile(
            file_name=file_name,
            mime_type="text/csv",
            extension="csv",
            content=content,
            size=len(content),
        )

    @staticmethod
    def _normalise_file_name(output_name: str) -> str:
        """Ensure the output file name ends with a ``.csv`` extension.

        Args:
            output_name: The requested file name from the configuration.

        Returns:
            The file name guaranteed to end with ``.csv`` (case-insensitive
            match; the extension is appended when missing).
        """
        name = (output_name or "document.csv").strip()
        if not name.lower().endswith(".csv"):
            name = f"{name}.csv"
        return name
