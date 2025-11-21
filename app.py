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
        "scoring": "3. Initial Scoring",
        "awaiting_selection": "4. Select Suggestions",
        "modification": "5. Modifying Resume",
        "rescoring": "6. Second Scoring",
        "optimization": "7. Optimizing Length",
        "validation": "8. Validating Format",
        "awaiting_approval": "9. Review & Approve",
        "export": "10. Exporting PDF",
        "completed": "11. Completed",
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


# Stage 5-7: Modification, Rescoring, Optimization & Validation
elif current_stage in ["modification", "rescoring", "optimization", "validation"]:
    st.header("Processing Resume Changes...")
    with st.spinner("Agents are working..."):
        if current_stage == "modification":
            st.info("Agent 2: Modifying your resume based on selected suggestions...")
        elif current_stage == "rescoring":
            st.info("Agent 3: Re-scoring the modified resume...")
        elif current_stage == "optimization":
            st.info("Agent 5: Optimizing resume length while maintaining score...")
        elif current_stage == "validation":
            st.info("Agent 4: Validating formatting and consistency...")


# Stage 9: Review Optimized Resume
elif current_stage == "awaiting_approval":
    state = st.session_state.workflow_state
    st.header("Step 3: Review & Approve Optimized Resume")

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

    # Display optimization info if available
    if state.get('optimized_resume'):
        st.subheader("Optimization Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Words Before",
                state.get('word_count_before', 'N/A')
            )

        with col2:
            st.metric(
                "Words After",
                state.get('word_count_after', 'N/A'),
                delta=f"-{state.get('words_removed', 0)}"
            )

        with col3:
            word_target = 600  # Target word count
            current_words = state.get('word_count_after', 0)
            if current_words <= word_target:
                st.success(f"✅ Within Target ({word_target} words)")
            else:
                st.warning(f"⚠️ Above Target ({word_target} words)")

        if state.get('optimization_summary'):
            with st.expander("Optimization Summary"):
                st.info(state['optimization_summary'])

        if state.get('optimization_changes'):
            with st.expander("Changes Made"):
                for change in state['optimization_changes']:
                    st.markdown(f"- {change}")

        st.divider()

    # Display side-by-side comparison
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original Resume")
        with st.expander("View Original", expanded=False):
            st.markdown(state['original_resume'])

    with col2:
        st.subheader("Optimized Resume")
        with st.expander("View Optimized", expanded=True):
            final_resume = state.get('optimized_resume') or state['modified_resume']
            st.markdown(final_resume)

    st.divider()

    # Display validation results if available
    if state.get('validation_score'):
        st.subheader("Validation Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Validation Score",
                f"{state['validation_score']}/10",
                help="Formatting and consistency score"
            )

        with col2:
            critical_count = state.get('critical_count', 0)
            warning_count = state.get('warning_count', 0)
            if critical_count > 0:
                st.metric("Critical Issues", critical_count, delta_color="inverse")
            elif warning_count > 0:
                st.metric("Warnings", warning_count, delta_color="inverse")
            else:
                st.metric("Issues", 0)

        with col3:
            if state.get('is_valid'):
                st.success("✅ Passes Validation")
            else:
                st.warning("⚠️ Has Issues")

        # Interactive validation recommendations
        if state.get('validation_recommendations'):
            st.markdown("### 📋 Apply Recommendations (Optional)")
            st.info("Check recommendations below to preview how they would improve your resume")

            # Create two columns: recommendations on left, preview on right
            rec_col, preview_col = st.columns([1, 1])

            with rec_col:
                st.markdown("**Select Fixes to Apply:**")

                # Initialize selected recommendations in session state
                if 'selected_validation_recs' not in st.session_state:
                    st.session_state.selected_validation_recs = []

                selected_recs = []
                for idx, rec in enumerate(state['validation_recommendations']):
                    is_selected = st.checkbox(
                        rec,
                        value=False,
                        key=f"val_rec_{idx}"
                    )
                    if is_selected:
                        selected_recs.append(rec)

                st.session_state.selected_validation_recs = selected_recs

                # Show issues in expandable section
                if state.get('validation_issues'):
                    with st.expander("View All Validation Issues", expanded=False):
                        critical = [i for i in state['validation_issues'] if i['severity'] == 'CRITICAL']
                        warnings = [i for i in state['validation_issues'] if i['severity'] == 'WARNING']
                        info = [i for i in state['validation_issues'] if i['severity'] == 'INFO']

                        if critical:
                            st.markdown("**🔴 Critical Issues:**")
                            for issue in critical:
                                st.markdown(f"- [{issue['category']}] {issue['description']}")

                        if warnings:
                            st.markdown("**🟡 Warnings:**")
                            for issue in warnings:
                                st.markdown(f"- [{issue['category']}] {issue['description']}")

                        if info:
                            st.markdown("**ℹ️ Info:**")
                            for issue in info:
                                st.markdown(f"- [{issue['category']}] {issue['description']}")

            with preview_col:
                st.markdown("**Resume Preview:**")

                # Get the current resume
                current_resume = state.get('optimized_resume') or state['modified_resume']

                # Show preview with selected recommendations highlighted
                if selected_recs:
                    st.info(f"✓ {len(selected_recs)} recommendation(s) selected")
                    st.caption("These improvements are noted for your reference. The current resume is shown below.")
                else:
                    st.caption("Select recommendations on the left to mark them for consideration")

                # Render the markdown preview in a scrollable container
                st.markdown("""
                <style>
                .resume-preview {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 20px;
                    background-color: white;
                    max-height: 600px;
                    overflow-y: auto;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                </style>
                """, unsafe_allow_html=True)

                with st.container():
                    st.markdown(f'<div class="resume-preview">', unsafe_allow_html=True)
                    st.markdown(current_resume)
                    st.markdown('</div>', unsafe_allow_html=True)

                # Show selected recommendations summary
                if selected_recs:
                    with st.expander("Selected Recommendations Summary", expanded=False):
                        st.markdown("You've selected these improvements:")
                        for rec in selected_recs:
                            st.markdown(f"✓ {rec}")

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


# Stage 9b: Legacy validation approval stage (shouldn't reach here anymore)
elif current_stage == "awaiting_validation_approval":
    # Redirect to awaiting_approval since validation is now shown there
    st.session_state.workflow_state['current_stage'] = "awaiting_approval"
    st.rerun()


# Stage 9c: Old validation check page (kept for backwards compatibility)
elif current_stage == "awaiting_validation_approval_old":
    state = st.session_state.workflow_state
    st.header("Step 4: Validation Results")

    # Display validation score
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Validation Score",
            f"{state['validation_score']}/10",
            help="Resume formatting and consistency score"
        )

    with col2:
        critical_count = state.get('critical_count', 0)
        warning_count = state.get('warning_count', 0)
        if critical_count > 0:
            st.metric("Critical Issues", critical_count, delta_color="inverse")
        elif warning_count > 0:
            st.metric("Warnings", warning_count, delta_color="inverse")
        else:
            st.metric("Issues", 0)

    with col3:
        if state['is_valid']:
            st.success("✅ Passes Validation")
        else:
            st.error("❌ Needs Fixes")

    st.divider()

    # Display validation summary
    if state.get('validation_summary'):
        st.subheader("Summary")
        st.info(state['validation_summary'])

    # Display issues if any
    if state.get('validation_issues'):
        st.subheader("Issues Found")

        # Group by severity
        critical = [i for i in state['validation_issues'] if i['severity'] == 'CRITICAL']
        warnings = [i for i in state['validation_issues'] if i['severity'] == 'WARNING']
        info = [i for i in state['validation_issues'] if i['severity'] == 'INFO']

        if critical:
            with st.expander(f"🔴 Critical Issues ({len(critical)})", expanded=True):
                for issue in critical:
                    st.markdown(f"**[{issue['category']}]** {issue['description']}")

        if warnings:
            with st.expander(f"🟡 Warnings ({len(warnings)})", expanded=True):
                for issue in warnings:
                    st.markdown(f"**[{issue['category']}]** {issue['description']}")

        if info:
            with st.expander(f"ℹ️ Informational ({len(info)})", expanded=False):
                for issue in info:
                    st.markdown(f"**[{issue['category']}]** {issue['description']}")

    # Display recommendations
    if state.get('validation_recommendations'):
        st.subheader("Recommendations")
        for rec in state['validation_recommendations']:
            st.markdown(f"- {rec}")

    st.divider()

    # Action buttons
    st.subheader("Next Steps")

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
        button_label = "✅ Proceed to Export" if state['is_valid'] else "⚠️ Export Anyway"
        button_type = "primary" if state['is_valid'] else "secondary"

        if st.button(button_label, type=button_type, use_container_width=True):
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


# Stage 10-11: Export & Completed
elif current_stage in ["export", "completed"]:
    state = st.session_state.workflow_state
    st.header("Step 4: Export Complete!")

    st.success("Resume approved and exported successfully!")

    # Display final resume
    with st.expander("View Final Resume", expanded=True):
        final_resume = state.get('optimized_resume') or state['modified_resume']
        st.markdown(final_resume)

    st.divider()

    # Export options
    st.subheader("Download Options")

    col1, col2 = st.columns(2)

    with col1:
        pdf_filename = st.text_input(
            "PDF Filename",
            value="optimized_resume.pdf",
            help="Enter the desired filename for your PDF"
        )

    with col2:
        md_filename = st.text_input(
            "Markdown Filename",
            value="optimized_resume.md",
            help="Enter the desired filename for your Markdown file"
        )

    # Download buttons
    col1, col2 = st.columns(2)

    with col1:
        if state.get('pdf_bytes'):
            st.download_button(
                label="📄 Download PDF",
                data=state['pdf_bytes'],
                file_name=pdf_filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
            st.caption(f"PDF saved to: {state.get('pdf_path', 'N/A')}")

    with col2:
        final_resume = state.get('optimized_resume') or state['modified_resume']
        if final_resume:
            st.download_button(
                label="📝 Download Markdown",
                data=final_resume,
                file_name=md_filename,
                mime="text/markdown",
                use_container_width=True,
                type="primary"
            )
            st.caption("Download the optimized resume as markdown")

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
