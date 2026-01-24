#!/usr/bin/env python3
"""
Test suite for Resume Customizer export workflow.

Run with: python test_export_workflow.py
"""

import os
import sys
import tempfile
import traceback
from pathlib import Path

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Sample data for testing
SAMPLE_RESUME = """# John Doe Resume

## Professional Summary
Experienced software engineer with 5+ years in full-stack development.

## Skills
- Python, JavaScript, React, Node.js
- AWS, GCP, Docker
- PostgreSQL, MongoDB

## Experience

### Senior Software Engineer - Tech Corp (2021-Present)
- Led team of 3 engineers in microservices architecture
- Improved API performance by 40%
- Mentored 2 junior developers

### Software Engineer - StartUp Inc (2019-2021)
- Developed full-stack web application
- Implemented automated testing (80% coverage)
- Deployed to AWS using Docker and Kubernetes

## Education
B.S. Computer Science - State University (2019)

## Certifications
- AWS Solutions Architect
"""

SAMPLE_JOB_DESCRIPTION = """
Senior Python Developer

We're looking for a Senior Python Developer to join our growing team.

Requirements:
- 5+ years of Python experience
- Strong knowledge of microservices architecture
- Experience with AWS and Docker
- Team mentoring skills
- Experience with automated testing

Nice to have:
- Kubernetes experience
- GCP experience
- Leadership experience
"""


def test_workflow_execution():
    """Test that the complete workflow can execute without errors."""
    print("\n" + "=" * 60)
    print("TEST 1: Complete Workflow Execution")
    print("=" * 60)

    try:
        from main import ResumeCustomizer

        customizer = ResumeCustomizer()
        print("✓ ResumeCustomizer initialized")

        # Test workflow start
        state = customizer.start_workflow(
            resume=SAMPLE_RESUME,
            job_description=SAMPLE_JOB_DESCRIPTION
        )
        print(f"✓ Workflow started, current_stage: {state.get('current_stage')}")
        print(f"  - Initial score: {state.get('initial_score')}")

        # Test workflow continuation (skip modification, just get to export)
        state['selected_suggestion_ids'] = list(range(len(state.get('suggestions', []))))
        state = customizer.continue_workflow(state)
        print(f"✓ Workflow continued, current_stage: {state.get('current_stage')}")
        print(f"  - New score: {state.get('new_score')}")

        # Test finalize (export)
        final_state = customizer.finalize_workflow(state)
        print(f"✓ Workflow finalized, current_stage: {final_state.get('current_stage')}")

        # Check for PDF bytes
        if final_state.get('pdf_bytes'):
            print(f"✓ PDF generated: {len(final_state['pdf_bytes'])} bytes")
        else:
            print("✗ ERROR: No PDF bytes in final state")
            return False

        return True

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        traceback.print_exc()
        return False


def test_export_pdf_generation():
    """Test that PDF export works correctly."""
    print("\n" + "=" * 60)
    print("TEST 2: PDF Export Generation")
    print("=" * 60)

    try:
        from utils.pdf_exporter import PDFExporter

        # Try to generate a PDF
        exporter = PDFExporter()
        pdf_bytes = exporter.markdown_to_pdf_bytes(
            markdown_content=SAMPLE_RESUME
        )

        if pdf_bytes:
            print(f"✓ PDF generated successfully: {len(pdf_bytes)} bytes")

            # Verify it's actually a PDF
            if pdf_bytes.startswith(b'%PDF'):
                print("✓ PDF header is valid")
                return True
            else:
                print("✗ ERROR: PDF header is invalid (first bytes: {pdf_bytes[:10]})")
                return False
        else:
            print("✗ ERROR: No PDF bytes returned")
            return False

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        traceback.print_exc()
        return False


def test_state_transitions():
    """Test that state transitions work correctly."""
    print("\n" + "=" * 60)
    print("TEST 3: State Transitions")
    print("=" * 60)

    try:
        from workflow.state import WorkflowState
        from main import ResumeCustomizer

        customizer = ResumeCustomizer()

        # Create initial state
        state = customizer.start_workflow(
            resume=SAMPLE_RESUME,
            job_description=SAMPLE_JOB_DESCRIPTION
        )

        # Check stage progression
        stages = []
        current = state.get('current_stage')
        stages.append(current)
        print(f"  Stage 1: {current}")

        # Continue through workflow
        state['selected_suggestion_ids'] = list(range(len(state.get('suggestions', []))))
        state = customizer.continue_workflow(state)
        current = state.get('current_stage')
        stages.append(current)
        print(f"  Stage 2: {current}")

        # Finalize
        state = customizer.finalize_workflow(state)
        current = state.get('current_stage')
        stages.append(current)
        print(f"  Stage 3: {current}")

        if 'awaiting_approval' in stages or 'validation_approval' in stages:
            print("✓ State transitions work correctly")
            return True
        else:
            print(f"✗ ERROR: Unexpected stage progression: {stages}")
            return False

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        traceback.print_exc()
        return False


def test_langfuse_initialization():
    """Test that Langfuse initialization works without errors."""
    print("\n" + "=" * 60)
    print("TEST 4: Langfuse Initialization")
    print("=" * 60)

    try:
        from utils.langfuse_config import configure_langfuse, is_langfuse_enabled

        client = configure_langfuse()
        enabled = is_langfuse_enabled()

        if enabled:
            print("✓ Langfuse is enabled and initialized")
        else:
            print("✓ Langfuse is disabled (OK for local testing)")

        return True

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        traceback.print_exc()
        return False


def test_tracing_wrapper():
    """Test that the tracing wrapper initializes correctly."""
    print("\n" + "=" * 60)
    print("TEST 5: Tracing Wrapper")
    print("=" * 60)

    try:
        from utils.langfuse_wrapper import initialize_tracing, get_tracing_status

        initialize_tracing()
        status = get_tracing_status()

        print(f"  Tracing Status:")
        print(f"    - LangSmith: {status['langsmith_enabled']}")
        print(f"    - Langfuse: {status['langfuse_enabled']}")
        print(f"    - Any enabled: {status['any_enabled']}")

        print("✓ Tracing wrapper initialized")
        return True

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Resume Customizer - Export Workflow Test Suite")
    print("=" * 60)

    tests = [
        ("Langfuse Initialization", test_langfuse_initialization),
        ("Tracing Wrapper", test_tracing_wrapper),
        ("PDF Export Generation", test_export_pdf_generation),
        ("State Transitions", test_state_transitions),
        ("Complete Workflow", test_workflow_execution),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ FATAL ERROR in {test_name}: {str(e)}")
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Safe to deploy.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Do not deploy.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
