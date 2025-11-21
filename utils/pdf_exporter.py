"""PDF export utility using ReportLab (Windows-compatible)."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import markdown
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
from html.parser import HTMLParser


class HTMLToFlowables(HTMLParser):
    """Parse HTML and convert to ReportLab flowables."""

    def __init__(self, styles):
        super().__init__()
        self.flowables = []
        self.styles = styles
        self.current_tag = None
        self.text_buffer = []
        self.list_items = []
        self.in_list = False

    def handle_starttag(self, tag, attrs):
        if tag in ['ul', 'ol']:
            self.in_list = True
        self.current_tag = tag

    def handle_endtag(self, tag):
        text = ''.join(self.text_buffer).strip()

        if text:
            if tag == 'h1':
                self.flowables.append(Paragraph(text, self.styles['Heading1']))
                self.flowables.append(Spacer(1, 0.1*inch))
            elif tag == 'h2':
                self.flowables.append(Spacer(1, 0.15*inch))
                self.flowables.append(Paragraph(text, self.styles['Heading2']))
                self.flowables.append(Spacer(1, 0.08*inch))
            elif tag == 'h3':
                self.flowables.append(Spacer(1, 0.1*inch))
                self.flowables.append(Paragraph(text, self.styles['Heading3']))
                self.flowables.append(Spacer(1, 0.05*inch))
            elif tag == 'p':
                self.flowables.append(Paragraph(text, self.styles['BodyText']))
                self.flowables.append(Spacer(1, 0.05*inch))
            elif tag == 'li':
                self.list_items.append(ListItem(Paragraph(text, self.styles['BodyText'])))
            elif tag in ['ul', 'ol']:
                if self.list_items:
                    bullet_type = 'bullet' if tag == 'ul' else '1'
                    self.flowables.append(ListFlowable(
                        self.list_items,
                        bulletType=bullet_type,
                        leftIndent=20
                    ))
                    self.flowables.append(Spacer(1, 0.05*inch))
                    self.list_items = []
                self.in_list = False

        self.text_buffer = []
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag:
            self.text_buffer.append(data)


class PDFExporter:
    """Exports markdown resumes to PDF format using ReportLab."""

    def __init__(self, output_dir: str = "data/resumes"):
        """
        Initialize PDF exporter.

        Args:
            output_dir: Directory to save PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = self._create_styles()

    def _create_styles(self):
        """Create custom styles for the resume."""
        styles = getSampleStyleSheet()

        # Heading 1 - Name
        styles.add(ParagraphStyle(
            name='Heading1',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=6,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Heading 2 - Section headers
        styles.add(ParagraphStyle(
            name='Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#2c3e50'),
            spaceAfter=4,
            spaceBefore=10,
            borderWidth=1,
            borderColor=HexColor('#bbbbbb'),
            borderPadding=2,
            fontName='Helvetica-Bold'
        ))

        # Heading 3 - Subsections
        styles.add(ParagraphStyle(
            name='Heading3',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=HexColor('#34495e'),
            spaceAfter=3,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        ))

        # Body text
        styles.add(ParagraphStyle(
            name='BodyText',
            parent=styles['BodyText'],
            fontSize=11,
            leading=14,
            textColor=HexColor('#333333'),
            fontName='Helvetica'
        ))

        return styles

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
            extensions=['extra', 'tables']
        )

        # Parse HTML and create flowables
        parser = HTMLToFlowables(self.styles)
        parser.feed(html_content)

        # Create PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        doc.build(parser.flowables)

        return str(output_path)

    def markdown_to_pdf_bytes(self, markdown_content: str) -> bytes:
        """
        Convert markdown to PDF bytes for download.

        Args:
            markdown_content: Markdown text

        Returns:
            PDF file as bytes
        """
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'tables']
        )

        # Parse HTML and create flowables
        parser = HTMLToFlowables(self.styles)
        parser.feed(html_content)

        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        doc.build(parser.flowables)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes
