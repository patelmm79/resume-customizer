"""PDF export utility using markdown-pdf."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from io import BytesIO
import tempfile
from markdown_pdf import MarkdownPdf, Section


class PDFExporter:
    """Exports markdown resumes to PDF format using markdown-pdf."""

    def __init__(self, output_dir: str = "data/resumes"):
        """
        Initialize PDF exporter.

        Args:
            output_dir: Directory to save PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load custom CSS from file
        css_path = Path(__file__).parent / "resume_style.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            self.custom_css = f.read()

    def markdown_to_pdf(
        self,
        markdown_content: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Convert markdown to PDF.

        Args:
            markdown_content: Markdown text
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved PDF file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resume_{timestamp}.pdf"

        if not filename.endswith(".pdf"):
            filename += ".pdf"

        output_path = self.output_dir / filename

        # Create PDF with custom CSS
        pdf = MarkdownPdf(toc_level=0)

        # Add custom CSS styling
        pdf.add_section(Section(markdown_content, toc=False), user_css=self.custom_css)

        # Save to file
        pdf.save(str(output_path))

        return str(output_path)

    def markdown_to_pdf_bytes(self, markdown_content: str) -> bytes:
        """
        Convert markdown to PDF bytes for download.

        Args:
            markdown_content: Markdown text

        Returns:
            PDF file as bytes
        """
        # Create temporary file for PDF generation
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Create PDF with custom CSS
            pdf = MarkdownPdf(toc_level=0)
            pdf.add_section(Section(markdown_content, toc=False), user_css=self.custom_css)
            pdf.save(tmp_path)

            # Read the PDF bytes
            with open(tmp_path, 'rb') as f:
                pdf_bytes = f.read()

            return pdf_bytes

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
