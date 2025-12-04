"""PDF export utility using markdown-pdf."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from io import BytesIO
import tempfile
from markdown_pdf import MarkdownPdf, Section
import re


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

        # Page layout constants (based on letter size with 0.75in margins)
        # Calibrated from actual PDF output: page breaks at line 51 of markdown
        # Accounting for line wrapping and visual spacing
        self.lines_per_page = 45  # Actual rendered lines per page (calibrated from PDF)
        self.chars_per_line = 120  # Approximate characters per line
        self.min_lines_for_section = 4  # Minimum lines to keep section together

    def _estimate_lines(self, text: str) -> int:
        """
        Estimate number of lines for a block of text.

        Args:
            text: Text content

        Returns:
            Estimated number of lines
        """
        # Split by newlines
        lines = text.split('\n')
        total_lines = 0

        for line in lines:
            if not line.strip():
                # Empty line counts as 1
                total_lines += 1
            elif line.startswith('#'):
                # Headings: count as 2 lines (heading + space)
                total_lines += 2
            elif line.startswith('***'):
                # Separator: counts as 1 line
                total_lines += 1
            elif line.startswith('*') or line.startswith('-'):
                # Bullet point: count as 1 line
                total_lines += 1
            else:
                # Regular text: estimate based on character count
                # Assume ~80-90 chars per line
                chars = len(line)
                total_lines += max(1, (chars // 120) + 1)

        return total_lines

    def _insert_page_breaks(self, markdown_content: str) -> str:
        """
        Insert page breaks to prevent sections from splitting awkwardly.

        Args:
            markdown_content: Original markdown content

        Returns:
            Markdown with page breaks inserted
        """
        lines = markdown_content.split('\n')
        result = []
        current_page_lines = 0
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this is a section header (## heading)
            if line.strip().startswith('## '):
                # Look ahead to count actual lines in this section
                section_lines = 2  # Heading + spacing
                j = i + 1

                # Count lines until next section or end, accounting for text wrapping
                while j < len(lines) and not lines[j].strip().startswith('## '):
                    line_text = lines[j].strip()
                    if line_text:
                        # Account for text wrapping on long lines
                        line_length = len(line_text)
                        if line_length > self.chars_per_line:
                            # Long line will wrap
                            wrapped_lines = (line_length // self.chars_per_line) + 1
                            section_lines += wrapped_lines
                        else:
                            section_lines += 1
                    j += 1

                # Decide if we need a page break
                # Only break if we're not at the very top of a page
                # Break conditions:
                # 1. Section fits on one page BUT would overflow current page
                # 2. Section is very large (>35 lines) and we're past the first few lines
                #
                # Don't break if section is small and will flow naturally

                section_fits_on_page = section_lines <= self.lines_per_page
                section_is_very_large = section_lines > 35  # Won't fit on one page
                would_overflow = (current_page_lines + section_lines) > self.lines_per_page
                past_minimum = current_page_lines > 5  # Not at very top

                # Small sections (that fit on one page) should stay together - break before them
                # Large sections will naturally span pages - let them flow
                needs_break = current_page_lines > 0 and (
                    (section_fits_on_page and would_overflow) or  # Small section needs break to stay together
                    (section_is_very_large and past_minimum)  # Very large section, give fresh page
                )

                if needs_break:
                    # Insert page break before section
                    result.append('<div style="page-break-before: always;"></div>')
                    result.append('')
                    current_page_lines = 0

                # Add the section header and count lines as we go
                result.append(line)
                current_page_lines += 2  # Heading takes ~2 lines with spacing
                i += 1

                # Now process the section content and track lines accurately
                while i < len(lines) and not lines[i].strip().startswith('## '):
                    line_text = lines[i].strip()
                    result.append(lines[i])
                    if line_text:
                        # Account for wrapping
                        if len(line_text) > self.chars_per_line:
                            wrapped = (len(line_text) // self.chars_per_line) + 1
                            current_page_lines += wrapped
                        else:
                            current_page_lines += 1
                    i += 1

            else:
                # Regular line (shouldn't reach here in section-based processing)
                result.append(line)
                if line.strip():
                    current_page_lines += 1
                i += 1

        return '\n'.join(result)

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

        # Use markdown as-is without automatic page break insertion
        # Page breaks should be manually added in the markdown with: <div style="page-break-before: always;"></div>

        # Create PDF with custom CSS
        pdf = MarkdownPdf(toc_level=0)

        # Add custom CSS styling
        pdf.add_section(Section(markdown_content, toc=False), user_css=self.custom_css)

        # Save to file
        pdf.save(str(output_path))

        return str(output_path)

    def markdown_to_pdf_bytes(
        self,
        markdown_content: str,
        font_size: float = 9.5,
        line_height: float = 1.2,
        page_margin: float = 0.75
    ) -> bytes:
        """
        Convert markdown to PDF bytes for download.

        Args:
            markdown_content: Markdown text
            font_size: Font size in pixels (default: 9.5)
            line_height: Line height as em multiplier (default: 1.2)
            page_margin: Page margin in inches (default: 0.75)

        Returns:
            PDF file as bytes
        """
        # Create temporary file for PDF generation
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Debug: Check if we're using non-default values
            import os
            debug_mode = os.getenv('DEBUG_MODE', '0') == '1'

            # ALWAYS print when non-default values are used
            print(f"[PDF Export] markdown_to_pdf_bytes called with: font_size={font_size}px, line_height={line_height}em, page_margin={page_margin}in")

            if debug_mode or (font_size != 9.5 or line_height != 1.2 or page_margin != 0.75):
                print(f"[PDF Export] Non-default values detected!")

            # Customize CSS with user-specified font size, line height, and margin
            # Note: CSS has leading spaces before properties in body selector
            custom_css = self.custom_css.replace(
                '  font-size:        9.5px;',
                f'  font-size:        {font_size}px;'
            ).replace(
                '  line-height:      1.2em;',
                f'  line-height:      {line_height}em;'
            ).replace(
                '  margin: 0.75in; /* Standard margins */',
                f'  margin: {page_margin}in; /* Standard margins */'
            )

            # Verify replacements happened - ALWAYS show this
            font_size_replaced = f'  font-size:        {font_size}px;' in custom_css
            line_height_replaced = f'  line-height:      {line_height}em;' in custom_css
            margin_replaced = f'  margin: {page_margin}in; /* Standard margins */' in custom_css

            print(f"[PDF Export] Replacements: font_size={font_size_replaced}, line_height={line_height_replaced}, margin={margin_replaced}")

            if not (font_size_replaced and line_height_replaced and margin_replaced):
                print(f"[PDF Export] WARNING: Some replacements failed!")
                print(f"[PDF Export] Searching for font-size in CSS...")
                if '9.5px' in custom_css:
                    print(f"[PDF Export] ERROR: Still contains default 9.5px!")

            # Create PDF with custom CSS
            pdf = MarkdownPdf(toc_level=0)
            pdf.add_section(Section(markdown_content, toc=False), user_css=custom_css)
            pdf.save(tmp_path)

            # Read the PDF bytes
            with open(tmp_path, 'rb') as f:
                pdf_bytes = f.read()

            return pdf_bytes

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
