"""Direct test of markdown-pdf with custom CSS."""
from markdown_pdf import MarkdownPdf, Section
import tempfile
from pathlib import Path

# Simple test CSS with VERY different values
test_css_small = """
body {
    font-size: 6px !important;
    line-height: 1.0 !important;
    color: red !important;
}

@page {
    margin: 0.25in !important;
}
"""

test_css_large = """
body {
    font-size: 16px !important;
    line-height: 2.0 !important;
    color: blue !important;
}

@page {
    margin: 1.5in !important;
}
"""

markdown_content = """# Test Document

This is a test paragraph to see if custom CSS is being applied properly.

## Section 1

- Item 1
- Item 2
- Item 3

## Section 2

More text here to fill the page and see the effects of different font sizes and line heights.
"""

def create_test_pdf(css, filename):
    """Create a PDF with custom CSS."""
    print(f"\nCreating {filename}...")

    pdf = MarkdownPdf(toc_level=0)
    pdf.add_section(Section(markdown_content, toc=False), user_css=css)
    pdf.save(filename)

    # Check file size
    file_size = Path(filename).stat().st_size
    print(f"  File size: {file_size} bytes")

print("=" * 60)
print("Testing markdown-pdf custom CSS")
print("=" * 60)

# Test 1: Small font + red
create_test_pdf(test_css_small, "test_css_small_red.pdf")

# Test 2: Large font + blue
create_test_pdf(test_css_large, "test_css_large_blue.pdf")

print("\n" + "=" * 60)
print("DONE - Open the PDFs to check if CSS was applied:")
print("  - test_css_small_red.pdf (should have 6px red text, 0.25in margins)")
print("  - test_css_large_blue.pdf (should have 16px blue text, 1.5in margins)")
print("=" * 60)
