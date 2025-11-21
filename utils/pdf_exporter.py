"""PDF export utility."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import markdown
from weasyprint import HTML, CSS
from io import BytesIO


class PDFExporter:
    """Exports markdown resumes to PDF format."""

    def __init__(self, output_dir: str = "data/resumes"):
        """
        Initialize PDF exporter.

        Args:
            output_dir: Directory to save PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'codehilite', 'tables']
        )

        # Add CSS styling for professional resume
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: letter;
                    margin: 0.75in;
                }}
                body {{
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                    color: #333;
                    max-width: 100%;
                }}
                h1 {{
                    font-size: 22pt;
                    font-weight: bold;
                    margin-bottom: 8pt;
                    margin-top: 0;
                    color: #1a1a1a;
                    border-bottom: 2px solid #333;
                    padding-bottom: 4pt;
                }}
                h2 {{
                    font-size: 14pt;
                    font-weight: bold;
                    margin-top: 12pt;
                    margin-bottom: 6pt;
                    color: #2c3e50;
                    border-bottom: 1px solid #bbb;
                    padding-bottom: 2pt;
                }}
                h3 {{
                    font-size: 12pt;
                    font-weight: bold;
                    margin-top: 8pt;
                    margin-bottom: 4pt;
                    color: #34495e;
                }}
                p {{
                    margin: 4pt 0;
                }}
                ul {{
                    margin: 4pt 0;
                    padding-left: 20pt;
                }}
                li {{
                    margin: 2pt 0;
                }}
                strong {{
                    font-weight: 600;
                }}
                a {{
                    color: #2c3e50;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Convert to PDF
        HTML(string=styled_html).write_pdf(output_path)

        return str(output_path)

    def markdown_to_pdf_bytes(self, markdown_content: str) -> bytes:
        """
        Convert markdown to PDF bytes for download.

        Args:
            markdown_content: Markdown text

        Returns:
            PDF file as bytes
        """
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'codehilite', 'tables']
        )

        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: letter;
                    margin: 0.75in;
                }}
                body {{
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                    color: #333;
                    max-width: 100%;
                }}
                h1 {{
                    font-size: 22pt;
                    font-weight: bold;
                    margin-bottom: 8pt;
                    margin-top: 0;
                    color: #1a1a1a;
                    border-bottom: 2px solid #333;
                    padding-bottom: 4pt;
                }}
                h2 {{
                    font-size: 14pt;
                    font-weight: bold;
                    margin-top: 12pt;
                    margin-bottom: 6pt;
                    color: #2c3e50;
                    border-bottom: 1px solid #bbb;
                    padding-bottom: 2pt;
                }}
                h3 {{
                    font-size: 12pt;
                    font-weight: bold;
                    margin-top: 8pt;
                    margin-bottom: 4pt;
                    color: #34495e;
                }}
                p {{
                    margin: 4pt 0;
                }}
                ul {{
                    margin: 4pt 0;
                    padding-left: 20pt;
                }}
                li {{
                    margin: 2pt 0;
                }}
                strong {{
                    font-weight: 600;
                }}
                a {{
                    color: #2c3e50;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        pdf_bytes = HTML(string=styled_html).write_pdf()
        return pdf_bytes
