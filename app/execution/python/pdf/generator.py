from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.execution.python.base.exceptions import EmptyPayloadError
from app.execution.python.base.file_generator import FileGenerator
from app.execution.python.base.generate_model import GeneratedFile


class PDFGeneratorService(FileGenerator):
    """Generate PDF files from a payload using ReportLab.

    This service implements the :class:`FileGenerator` contract. It turns a
    payload into a list of ReportLab flowables (the "story"), renders that
    story into PDF bytes, and wraps the result in a :class:`GeneratedFile`.
    """

    def generate(self, payload: dict, configuration: dict) -> GeneratedFile:
        """Build a PDF file from the given payload.

        Args:
            payload: The data used to populate the PDF content.
            configuration: Generation options such as the output file name.

        Returns:
            The generated PDF wrapped in a :class:`GeneratedFile`.

        Raises:
            EmptyPayloadError: If ``payload`` is empty or falsy.
        """
        if not payload:
            raise EmptyPayloadError(self.__class__.__name__)

        story = self._build_story(payload, configuration)
        pdf = self._build_pdf(story)
        return self._create_generated_file(pdf, configuration)

    def _build_story(self, payload: dict, configuration: dict) -> list:
        """Build the list of ReportLab flowables for the document.

        Renders a title followed by a set of labelled fields. Missing values
        fall back to ``"-"`` so the document is always well formed.

        Args:
            payload: The data used to populate the PDF content.
            configuration: Generation options that influence the layout.

        Returns:
            A list of ReportLab flowables to be rendered by the document.
        """
        styles = getSampleStyleSheet()
        story: list = []

        title = configuration.get("title", "Loan Statement")
        story.append(Paragraph(title, styles["Title"]))
        story.append(Spacer(1, 12))

        fields = [
            ("Customer Name", "customer_name"),
            ("Loan Number", "loan_number"),
            ("Branch", "branch"),
        ]
        for label, key in fields:
            value = payload.get(key) or "-"
            story.append(
                Paragraph(f"<b>{label}:</b> {value}", styles["Normal"])
            )
            story.append(Spacer(1, 6))

        return story

    def _build_pdf(self, story: list) -> bytes:
        """Render a story of flowables into PDF bytes.

        Args:
            story: The list of ReportLab flowables to render.

        Returns:
            The rendered PDF document as raw bytes.
        """
        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=A4)
        document.build(story)

        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def _create_generated_file(
        self, pdf: bytes, configuration: dict
    ) -> GeneratedFile:
        """Wrap raw PDF bytes in a :class:`GeneratedFile`.

        Args:
            pdf: The rendered PDF document as raw bytes.
            configuration: Generation options; ``output_name`` sets the file
                name and defaults to ``"document.pdf"``.

        Returns:
            The PDF bytes wrapped with file metadata.
        """
        file_name = self._normalise_file_name(
            configuration.get("output_name", "document.pdf")
        )

        return GeneratedFile(
            file_name=file_name,
            mime_type="application/pdf",
            extension="pdf",
            content=pdf,
            size=len(pdf),
        )

    @staticmethod
    def _normalise_file_name(output_name: str) -> str:
        """Ensure the output file name ends with a ``.pdf`` extension.

        Args:
            output_name: The requested file name from the configuration.

        Returns:
            The file name guaranteed to end with ``.pdf`` (case-insensitive
            match; the extension is appended when missing).
        """
        name = (output_name or "document.pdf").strip()
        if not name.lower().endswith(".pdf"):
            name = f"{name}.pdf"
        return name
