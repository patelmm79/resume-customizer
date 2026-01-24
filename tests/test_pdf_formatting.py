"""Test script to verify PDF formatting parameters are working."""
from utils.pdf_exporter import PDFExporter
from pathlib import Path

# Sample markdown content
sample_markdown = """# John Doe

**Software Engineer** | john@example.com | (555) 123-4567

---

## Summary

Experienced software engineer with 5 years of experience in full-stack development.

## Experience

### Senior Software Engineer | Tech Corp
*Jan 2020 - Present*

- Led development of microservices architecture
- Improved system performance by 40%
- Mentored junior developers

### Software Engineer | StartupCo
*Jun 2018 - Dec 2019*

- Built RESTful APIs using Python and Flask
- Implemented CI/CD pipelines
- Collaborated with cross-functional teams

## Skills

- Python, JavaScript, TypeScript
- React, Node.js, Django
- AWS, Docker, Kubernetes
"""

def test_pdf_export():
    """Test PDF export with different formatting options."""
    exporter = PDFExporter()

    print("=" * 60)
    print("TEST 1: Default formatting (9.5px, 1.2em, 0.75in)")
    print("=" * 60)

    pdf_bytes1 = exporter.markdown_to_pdf_bytes(
        sample_markdown,
        font_size=9.5,
        line_height=1.2,
        page_margin=0.75
    )

    # Save to file for inspection
    test_file1 = Path("test_output_default.pdf")
    with open(test_file1, 'wb') as f:
        f.write(pdf_bytes1)
    print(f"[OK] Saved to {test_file1} (size: {len(pdf_bytes1)} bytes)")

    print("\n" + "=" * 60)
    print("TEST 2: Small formatting (8.0px, 1.1em, 0.5in)")
    print("=" * 60)

    pdf_bytes2 = exporter.markdown_to_pdf_bytes(
        sample_markdown,
        font_size=8.0,
        line_height=1.1,
        page_margin=0.5
    )

    # Save to file for inspection
    test_file2 = Path("test_output_small.pdf")
    with open(test_file2, 'wb') as f:
        f.write(pdf_bytes2)
    print(f"[OK] Saved to {test_file2} (size: {len(pdf_bytes2)} bytes)")

    print("\n" + "=" * 60)
    print("TEST 3: Large formatting (11.0px, 1.4em, 1.0in)")
    print("=" * 60)

    pdf_bytes3 = exporter.markdown_to_pdf_bytes(
        sample_markdown,
        font_size=11.0,
        line_height=1.4,
        page_margin=1.0
    )

    # Save to file for inspection
    test_file3 = Path("test_output_large.pdf")
    with open(test_file3, 'wb') as f:
        f.write(pdf_bytes3)
    print(f"[OK] Saved to {test_file3} (size: {len(pdf_bytes3)} bytes)")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Default PDF: {len(pdf_bytes1)} bytes")
    print(f"Small PDF:   {len(pdf_bytes2)} bytes")
    print(f"Large PDF:   {len(pdf_bytes3)} bytes")
    print("\nPlease open the test PDFs to verify formatting changes:")
    print(f"  - {test_file1}")
    print(f"  - {test_file2}")
    print(f"  - {test_file3}")

if __name__ == "__main__":
    test_pdf_export()
