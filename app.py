"""Streamlit frontend for Resume Customizer."""
import streamlit as st
from pathlib import Path
import traceback

from agents.agent_1_scorer import ResumeScorerAgent
from agents.agent_2_modifier import ResumeModifierAgent
from agents.agent_3_rescorer import ResumeRescorerAgent
from utils.job_scraper import JobScraper
from utils.pdf_exporter import PDFExporter


# Page configuration
st.set_page_config(
    page_title="Resume Customizer",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "original_resume" not in st.session_state:
    st.session_state.original_resume = None
if "job_description" not in st.session_state:
    st.session_state.job_description = None
if "scoring_result" not in st.session_state:
    st.session_state.scoring_result = None
if "modified_resume" not in st.session_state:
    st.session_state.modified_resume = None
if "rescoring_result" not in st.session_state:
    st.session_state.rescoring_result = None


def reset_app():
    """Reset the application state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.stage = "input"
    st.rerun()


# Header
st.title("📄 Resume Customizer")
st.markdown("### AI-Powered Resume Optimization System")
st.divider()

# Sidebar
with st.sidebar:
    st.header("Workflow Stages")
    stages = {
        "input": "1. Input Resume & Job",
        "scoring": "2. Initial Scoring",
        "modification": "3. Resume Modification",
        "rescoring": "4. Re-scoring & Approval",
        "export": "5. Export PDF"
    }

    for stage_key, stage_name in stages.items():
        if st.session_state.stage == stage_key:
            st.markdown(f"**➡️ {stage_name}**")
        else:
            st.markdown(f"   {stage_name}")

    st.divider()
    if st.button("🔄 Start Over", use_container_width=True):
        reset_app()

    st.divider()
    st.caption("Built with Streamlit & Google Gemini")


# Stage 1: Input
if st.session_state.stage == "input":
    st.header("Step 1: Upload Resume & Job Description")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Resume Upload")
        uploaded_file = st.file_uploader(
            "Upload your resume (Markdown format)",
            type=["md", "txt"],
            help="Upload a markdown file containing your resume"
        )

        if uploaded_file:
            resume_content = uploaded_file.read().decode("utf-8")
            st.session_state.original_resume = resume_content
            with st.expander("Preview Resume"):
                st.markdown(resume_content)

    with col2:
        st.subheader("Job Description")
        job_url = st.text_input(
            "Job posting URL",
            placeholder="https://example.com/job-posting"
        )

        manual_input = st.text_area(
            "Or paste job description manually",
            height=200,
            placeholder="Paste the job description here..."
        )

        if st.button("Fetch from URL", disabled=not job_url):
            with st.spinner("Fetching job description..."):
                try:
                    scraper = JobScraper()
                    job_desc = scraper.fetch_job_description(job_url)
                    st.session_state.job_description = job_desc
                    st.success("Job description fetched successfully!")
                    with st.expander("Preview Job Description"):
                        st.text(job_desc[:500] + "...")
                except Exception as e:
                    st.error(f"Error fetching job description: {str(e)}")

        if manual_input:
            st.session_state.job_description = manual_input

    st.divider()

    if st.session_state.original_resume and st.session_state.job_description:
        if st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
            st.session_state.stage = "scoring"
            st.rerun()
    else:
        st.info("Please upload a resume and provide a job description to continue.")


# Stage 2: Initial Scoring
elif st.session_state.stage == "scoring":
    st.header("Step 2: Resume Analysis & Scoring")

    with st.spinner("Agent 1 is analyzing your resume..."):
        try:
            agent1 = ResumeScorerAgent()
            result = agent1.analyze_and_score(
                st.session_state.original_resume,
                st.session_state.job_description
            )
            st.session_state.scoring_result = result

            # Display results
            col1, col2, col3 = st.columns([1, 2, 2])

            with col1:
                st.metric(
                    "Compatibility Score",
                    f"{result['score']}/10",
                    help="How well your resume matches the job"
                )

            with col2:
                st.subheader("Analysis")
                st.info(result['analysis'])

            with col3:
                # Score interpretation
                score = result['score']
                if score >= 8:
                    st.success("Excellent match! Minor improvements suggested.")
                elif score >= 6:
                    st.warning("Good foundation. Improvements will help.")
                else:
                    st.error("Significant improvements needed for better match.")

            st.divider()

            # Suggestions with checkboxes
            st.subheader("Suggested Improvements")
            st.markdown("Select the changes you want to apply:")

            # Group suggestions by category
            categories = {}
            for suggestion in result['suggestions']:
                category = suggestion['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(suggestion)

            # Display suggestions by category
            for category, suggestions in categories.items():
                with st.expander(f"📌 {category} ({len(suggestions)} suggestions)", expanded=True):
                    for suggestion in suggestions:
                        suggestion['selected'] = st.checkbox(
                            suggestion['text'],
                            value=True,
                            key=f"suggestion_{suggestion['id']}"
                        )

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Back to Input", use_container_width=True):
                    st.session_state.stage = "input"
                    st.rerun()

            with col2:
                if st.button("➡️ Apply Changes", type="primary", use_container_width=True):
                    st.session_state.stage = "modification"
                    st.rerun()

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.code(traceback.format_exc())
            if st.button("⬅️ Back to Input"):
                st.session_state.stage = "input"
                st.rerun()


# Stage 3: Modification
elif st.session_state.stage == "modification":
    st.header("Step 3: Resume Modification")

    with st.spinner("Agent 2 is modifying your resume..."):
        try:
            agent2 = ResumeModifierAgent()
            modified = agent2.modify_resume(
                st.session_state.original_resume,
                st.session_state.scoring_result['suggestions'],
                st.session_state.job_description
            )
            st.session_state.modified_resume = modified

            st.success("Resume modified successfully!")

            # Display side-by-side comparison
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Original Resume")
                st.markdown(st.session_state.original_resume)

            with col2:
                st.subheader("Modified Resume")
                st.markdown(modified)

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Back to Scoring", use_container_width=True):
                    st.session_state.stage = "scoring"
                    st.rerun()

            with col2:
                if st.button("➡️ Re-score Resume", type="primary", use_container_width=True):
                    st.session_state.stage = "rescoring"
                    st.rerun()

        except Exception as e:
            st.error(f"Error during modification: {str(e)}")
            st.code(traceback.format_exc())
            if st.button("⬅️ Back to Scoring"):
                st.session_state.stage = "scoring"
                st.rerun()


# Stage 4: Re-scoring
elif st.session_state.stage == "rescoring":
    st.header("Step 4: Re-scoring & Approval")

    with st.spinner("Agent 3 is evaluating the modified resume..."):
        try:
            agent3 = ResumeRescorerAgent()
            result = agent3.rescore_resume(
                st.session_state.modified_resume,
                st.session_state.job_description,
                st.session_state.scoring_result['score']
            )
            st.session_state.rescoring_result = result

            # Display score comparison
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Original Score",
                    f"{result['original_score']}/10"
                )

            with col2:
                st.metric(
                    "New Score",
                    f"{result['new_score']}/10",
                    delta=f"+{result['score_improvement']}" if result['score_improvement'] > 0 else str(result['score_improvement'])
                )

            with col3:
                if result['recommendation'] == "Ready to Submit":
                    st.success("✅ Ready to Submit")
                else:
                    st.warning("⚠️ Needs More Work")

            st.divider()

            # Comparison and improvements
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Improvements Made")
                if result['improvements']:
                    for improvement in result['improvements']:
                        st.markdown(f"✅ {improvement}")
                else:
                    st.info("Changes have been applied based on your selections.")

            with col2:
                if result['concerns']:
                    st.subheader("Remaining Concerns")
                    for concern in result['concerns']:
                        st.markdown(f"⚠️ {concern}")

            with st.expander("Detailed Reasoning"):
                st.write(result['reasoning'])

            st.divider()

            # Approval
            st.subheader("Approval")
            st.markdown("Are you satisfied with this version?")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("⬅️ Go Back to Modify", use_container_width=True):
                    st.session_state.stage = "modification"
                    st.rerun()

            with col2:
                if st.button("🔄 Re-score Again", use_container_width=True):
                    st.session_state.stage = "scoring"
                    st.rerun()

            with col3:
                if st.button("✅ Approve & Export", type="primary", use_container_width=True):
                    st.session_state.stage = "export"
                    st.rerun()

        except Exception as e:
            st.error(f"Error during re-scoring: {str(e)}")
            st.code(traceback.format_exc())
            if st.button("⬅️ Back to Modification"):
                st.session_state.stage = "modification"
                st.rerun()


# Stage 5: Export
elif st.session_state.stage == "export":
    st.header("Step 5: Export to PDF")

    st.success("Resume approved! Ready to export.")

    # Display final resume
    with st.expander("View Final Resume", expanded=True):
        st.markdown(st.session_state.modified_resume)

    st.divider()

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        filename = st.text_input(
            "PDF Filename",
            value="optimized_resume.pdf",
            help="Enter the desired filename for your PDF"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing

        if st.button("💾 Save as PDF", type="primary", use_container_width=True):
            try:
                exporter = PDFExporter()
                pdf_path = exporter.markdown_to_pdf(
                    st.session_state.modified_resume,
                    filename
                )
                st.success(f"PDF saved successfully!")
                st.info(f"Location: {pdf_path}")

            except Exception as e:
                st.error(f"Error exporting PDF: {str(e)}")
                st.code(traceback.format_exc())

    # Download button
    try:
        exporter = PDFExporter()
        pdf_bytes = exporter.markdown_to_pdf_bytes(st.session_state.modified_resume)

        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error creating download: {str(e)}")

    st.divider()

    # Summary
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Original Score", f"{st.session_state.scoring_result['score']}/10")

    with col2:
        st.metric("Final Score", f"{st.session_state.rescoring_result['new_score']}/10")

    with col3:
        improvement = st.session_state.rescoring_result['score_improvement']
        st.metric("Improvement", f"+{improvement}" if improvement > 0 else str(improvement))

    st.divider()

    if st.button("🎉 Start New Resume", type="primary", use_container_width=True):
        reset_app()
