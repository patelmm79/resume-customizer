"""Streamlit frontend for Resume Customizer with LangGraph orchestration."""
import streamlit as st
from pathlib import Path
import traceback

from main import ResumeCustomizer
from workflow.state import WorkflowState


# Page configuration
st.set_page_config(
    page_title="Resume Customizer (LangGraph)",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = None
if "customizer" not in st.session_state:
    st.session_state.customizer = ResumeCustomizer()


def reset_app():
    """Reset the application state."""
    st.session_state.workflow_state = None
    st.rerun()


def get_current_stage():
    """Get the current workflow stage."""
    if st.session_state.workflow_state is None:
        return "input"
    return st.session_state.workflow_state.get("current_stage", "input")


# Header
st.title("📄 Resume Customizer")
st.markdown("### AI-Powered Resume Optimization with LangGraph")
st.divider()

# Sidebar
with st.sidebar:
    st.header("Workflow Stages")

    current_stage = get_current_stage()

    stages_map = {
        "input": "1. Input Resume & Job",
        "fetch_job": "2. Fetching Job Description",
        "scoring": "3. Analyzing & Scoring",
        "awaiting_selection": "4. Select Suggestions",
        "modification": "5. Modifying Resume",
        "rescoring": "6. Re-scoring",
        "awaiting_approval": "7. Approval",
        "export": "8. Exporting PDF",
        "completed": "9. Completed",
        "error": "❌ Error"
    }

    for stage_key, stage_name in stages_map.items():
        if current_stage == stage_key:
            st.markdown(f"**➡️ {stage_name}**")
        else:
            st.markdown(f"   {stage_name}")

    st.divider()
    if st.button("🔄 Start Over", use_container_width=True):
        reset_app()

    st.divider()
    st.caption("Built with Streamlit, LangGraph & Gemini")


# Main workflow
current_stage = get_current_stage()

# Stage 1: Input
if current_stage == "input":
    st.header("Step 1: Upload Resume & Job Description")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Resume Upload")
        uploaded_file = st.file_uploader(
            "Upload your resume (Markdown format)",
            type=["md", "txt"],
            help="Upload a markdown file containing your resume"
        )

        resume_content = None
        if uploaded_file:
            resume_content = uploaded_file.read().decode("utf-8")
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

    st.divider()

    if resume_content and (job_url or manual_input):
        if st.button("🚀 Start Workflow", type="primary", use_container_width=True):
            with st.spinner("Starting workflow..."):
                try:
                    state = st.session_state.customizer.start_workflow(
                        resume=resume_content,
                        job_description=manual_input if manual_input else None,
                        job_url=job_url if job_url else None
                    )
                    st.session_state.workflow_state = state
                    st.rerun()
                except Exception as e:
                    st.error(f"Error starting workflow: {str(e)}")
                    st.code(traceback.format_exc())
    else:
        st.info("Please upload a resume and provide a job description to continue.")


# Stage 2-3: Analysis & Scoring
elif current_stage in ["fetch_job", "scoring"]:
    st.header("Analyzing Resume...")
    with st.spinner("Agents are working..."):
        st.info("Workflow is processing. This may take a moment.")


# Stage 4: Suggestion Selection
elif current_stage == "awaiting_selection":
    state = st.session_state.workflow_state
    st.header("Step 2: Review Analysis & Select Suggestions")

    # Display score
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        st.metric(
            "Compatibility Score",
            f"{state['initial_score']}/10",
            help="How well your resume matches the job"
        )

    with col2:
        st.subheader("Analysis")
        st.info(state['analysis'])

    with col3:
        score = state['initial_score']
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
    for suggestion in state['suggestions']:
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
                    value=suggestion['selected'],
                    key=f"suggestion_{suggestion['id']}"
                )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Input", use_container_width=True):
            st.session_state.workflow_state = None
            st.rerun()

    with col2:
        if st.button("➡️ Apply Changes", type="primary", use_container_width=True):
            with st.spinner("Applying modifications..."):
                try:
                    # Update state with current selections
                    st.session_state.workflow_state['suggestions'] = state['suggestions']

                    # Continue workflow
                    updated_state = st.session_state.customizer.continue_workflow(
                        st.session_state.workflow_state
                    )
                    st.session_state.workflow_state = updated_state
                    st.rerun()
                except Exception as e:
                    st.error(f"Error applying modifications: {str(e)}")
                    st.code(traceback.format_exc())


# Stage 5-6: Modification & Rescoring
elif current_stage in ["modification", "rescoring"]:
    st.header("Processing Resume Changes...")
    with st.spinner("Agents are working..."):
        st.info("Modifying and rescoring your resume. Please wait...")


# Stage 7: Approval
elif current_stage == "awaiting_approval":
    state = st.session_state.workflow_state
    st.header("Step 3: Review Results & Approve")

    # Display score comparison
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Original Score",
            f"{state['initial_score']}/10"
        )

    with col2:
        improvement = state['score_improvement']
        st.metric(
            "New Score",
            f"{state['new_score']}/10",
            delta=f"+{improvement}" if improvement > 0 else str(improvement)
        )

    with col3:
        if state['recommendation'] == "Ready to Submit":
            st.success("✅ Ready to Submit")
        else:
            st.warning("⚠️ Needs More Work")

    st.divider()

    # Display side-by-side comparison
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original Resume")
        with st.expander("View Original", expanded=False):
            st.markdown(state['original_resume'])

    with col2:
        st.subheader("Modified Resume")
        with st.expander("View Modified", expanded=True):
            st.markdown(state['modified_resume'])

    st.divider()

    # Improvements and concerns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Improvements Made")
        if state['improvements']:
            for improvement in state['improvements']:
                st.markdown(f"✅ {improvement}")
        else:
            st.info("Changes have been applied based on your selections.")

    with col2:
        if state.get('concerns'):
            st.subheader("Remaining Concerns")
            for concern in state['concerns']:
                st.markdown(f"⚠️ {concern}")

    with st.expander("Detailed Reasoning"):
        st.write(state['reasoning'])

    st.divider()

    # Approval
    st.subheader("Approval")
    st.markdown("Are you satisfied with this version?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅️ Start Over", use_container_width=True):
            reset_app()

    with col2:
        if st.button("🔄 Reselect Suggestions", use_container_width=True):
            # Go back to suggestion selection
            st.session_state.workflow_state['current_stage'] = "awaiting_selection"
            st.rerun()

    with col3:
        if st.button("✅ Approve & Export", type="primary", use_container_width=True):
            with st.spinner("Exporting to PDF..."):
                try:
                    final_state = st.session_state.customizer.finalize_workflow(
                        st.session_state.workflow_state
                    )
                    st.session_state.workflow_state = final_state
                    st.rerun()
                except Exception as e:
                    st.error(f"Error exporting: {str(e)}")
                    st.code(traceback.format_exc())


# Stage 8-9: Export & Completed
elif current_stage in ["export", "completed"]:
    state = st.session_state.workflow_state
    st.header("Step 4: Export Complete!")

    st.success("Resume approved and exported successfully!")

    # Display final resume
    with st.expander("View Final Resume", expanded=True):
        st.markdown(state['modified_resume'])

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
        st.write("")
        st.write("")

    # Download button
    if state.get('pdf_bytes'):
        st.download_button(
            label="⬇️ Download PDF",
            data=state['pdf_bytes'],
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

        st.info(f"PDF saved to: {state.get('pdf_path', 'N/A')}")

    st.divider()

    # Summary
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Original Score", f"{state['initial_score']}/10")

    with col2:
        st.metric("Final Score", f"{state['new_score']}/10")

    with col3:
        improvement = state['score_improvement']
        st.metric("Improvement", f"+{improvement}" if improvement > 0 else str(improvement))

    st.divider()

    if st.button("🎉 Start New Resume", type="primary", use_container_width=True):
        reset_app()


# Error state
elif current_stage == "error":
    state = st.session_state.workflow_state
    st.header("❌ Error Occurred")

    st.error(f"An error occurred: {state.get('error', 'Unknown error')}")

    if st.button("🔄 Start Over", type="primary"):
        reset_app()
