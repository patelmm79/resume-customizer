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
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = "gemini"
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None


def reset_app():
    """Reset the application state."""
    st.session_state.workflow_state = None
    st.rerun()


def get_current_stage():
    """Get the current workflow stage."""
    if st.session_state.workflow_state is None:
        return "input"
    return st.session_state.workflow_state.get("current_stage", "input")


# Compact Header
header_col1, header_col2 = st.columns([1, 3])
with header_col1:
    st.markdown("## 📄 Resume Customizer")
with header_col2:
    st.markdown("*AI-Powered Resume Optimization with LangGraph*")

# Score Tracker - ALWAYS VISIBLE (persistent across all stages after initial scoring)
if st.session_state.workflow_state and st.session_state.workflow_state.get("initial_score") is not None:
    state = st.session_state.workflow_state

    st.markdown("---")
    st.markdown("#### 📊 Score Evolution")

    score_cols = st.columns(5)

    with score_cols[0]:
        st.metric(
            "Initial Score",
            f"{state['initial_score']}/100",
            help="Original resume compatibility with job description"
        )

    with score_cols[1]:
        if state.get("new_score") is not None:
            improvement = state['new_score'] - state['initial_score']
            st.metric(
                "After Modifications",
                f"{state['new_score']}/100",
                delta=f"+{improvement}" if improvement > 0 else str(improvement),
                help="Score after applying Agent 1 suggestions"
            )
        else:
            st.metric("After Modifications", "—", help="Not yet calculated")

    with score_cols[2]:
        # After optimization - show the SCORE at this stage (same as new_score since optimization doesn't change score)
        if state.get("new_score") is not None:
            st.metric(
                "After Optimization",
                f"{state['new_score']}/100",
                delta="0" if state.get("optimized_resume") else None,
                help="Score maintained after optimization (conciseness improved)"
            )
        else:
            st.metric("After Optimization", "—", help="Not yet calculated")

    with score_cols[3]:
        # After Round 2 - show the SCORE (still same as new_score)
        if state.get("optimized_resume_round2") is not None:
            st.metric(
                "After Round 2",
                f"{state['new_score']}/100",
                delta="0",
                help="Score maintained after Round 2 optimization"
            )
        else:
            st.metric("After Round 2", "—", help="Not yet calculated")

    with score_cols[4]:
        if state.get("final_score") is not None:
            total_improvement = state['final_score'] - state['initial_score']
            st.metric(
                "Final Score",
                f"{state['final_score']}/100",
                delta=f"+{total_improvement}" if total_improvement > 0 else str(total_improvement),
                help="Final compatibility score after all edits"
            )
        else:
            st.metric("Final Score", "—", help="Not yet calculated")

st.divider()

# Sidebar
with st.sidebar:
    st.header("⚙️ LLM Configuration")

    # Import model configuration (get fresh list to support dynamic .env config)
    from utils.llm_client import get_available_models
    AVAILABLE_MODELS = get_available_models()

    # Provider selection
    provider = st.selectbox(
        "LLM Provider",
        options=["gemini", "claude", "custom"],
        index=["gemini", "claude", "custom"].index(st.session_state.selected_provider),
        help="Select the LLM provider to use for resume customization",
        key="provider_selector"
    )

    # Update session state
    if provider != st.session_state.selected_provider:
        st.session_state.selected_provider = provider
        st.session_state.selected_model = None  # Reset model selection

    # Model selection based on provider
    available_models = AVAILABLE_MODELS.get(provider, [])

    if available_models:
        model = st.selectbox(
            "Model",
            options=available_models,
            help=f"Select the specific {provider} model to use",
            key="model_selector"
        )
        st.session_state.selected_model = model

    # Show configuration status
    import os
    from dotenv import load_dotenv
    load_dotenv()

    config_status = "✅ Configured"
    if provider == "gemini":
        if not os.getenv("GEMINI_API_KEY"):
            config_status = "❌ Missing GEMINI_API_KEY"
    elif provider == "claude":
        if not os.getenv("ANTHROPIC_API_KEY"):
            config_status = "❌ Missing ANTHROPIC_API_KEY"
    elif provider == "custom":
        if not os.getenv("CUSTOM_LLM_API_KEY") or not os.getenv("CUSTOM_LLM_BASE_URL"):
            config_status = "❌ Missing API config"

    st.caption(f"Status: {config_status}")

    st.divider()
    st.header("Workflow Stages")

    current_stage = get_current_stage()

    stages_map = {
        "input": "1. Input Resume & Job",
        "fetch_job": "2. Fetching Job Description",
        "scoring": "3. Initial Scoring",
        "awaiting_selection": "4. Select Suggestions",
        "modification": "5. Modifying Resume",
        "rescoring": "6. Second Scoring",
        "optimization": "7. Analyzing Length (R1)",
        "awaiting_optimization_selection": "8. Select Optimizations (R1)",
        "applying_optimizations": "9. Applying Optimizations (R1)",
        "optimization_round2": "10. Analyzing Length (R2)",
        "awaiting_optimization_selection_round2": "11. Select Optimizations (R2)",
        "applying_optimizations_round2": "12. Applying Optimizations (R2)",
        "validation": "13. Validating Format",
        "awaiting_approval": "14. Review & Approve",
        "freeform_editing": "15. Final Edits (Optional)",
        "final_scoring": "16. Final Score",
        "export": "17. Exporting PDF",
        "cover_letter_ready": "18. Cover Letter Generated",
        "cover_letter_reviewed": "19. Cover Letter Reviewed",
        "cover_letter_revised": "20. Cover Letter Revised",
        "completed": "21. Completed",
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
            f"{state['initial_score']}/100",
            help="How well your resume matches the job"
        )

    with col2:
        st.subheader("Analysis")
        st.info(state['analysis'])

    with col3:
        score = state['initial_score']
        if score >= 80:
            st.success("Excellent match! Minor improvements suggested.")
        elif score >= 60:
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
            # Add Select All checkbox for this category
            select_all_key = f"select_all_{category.replace(' ', '_')}"

            # Use checkbox with key - don't set value if using key
            select_all = st.checkbox(
                "✅ Select All",
                value=False,  # Default to unselected for initial suggestions
                key=select_all_key
            )

            st.divider()

            # Check if this category needs text boxes (Summary and Experience)
            needs_text_box = category in ["Summary", "Experience", "Professional Experience"]

            for suggestion in suggestions:
                # Use Select All state if checked, otherwise default to unchecked
                default_value = select_all if select_all else False

                if needs_text_box:
                    # Create two columns: checkbox/description on left, text box on right
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        # Checkbox shows the description (justification)
                        suggestion['selected'] = st.checkbox(
                            suggestion['text'],
                            value=default_value,
                            key=f"suggestion_{suggestion['id']}"
                        )

                    with col2:
                        # Only show text box if checkbox is selected
                        if suggestion['selected']:
                            # Text box shows the actual suggested text (pre-populated)
                            suggestion['edited_text'] = st.text_area(
                                f"Edit suggestion #{suggestion['id']}",
                                value=suggestion.get('edited_text', suggestion['text']),
                                height=100,
                                key=f"edit_{suggestion['id']}",
                                help="Edit the suggested text before applying",
                                label_visibility="collapsed"
                            )
                        else:
                            # Show a preview of the suggested text when not selected
                            preview_text = suggestion.get('edited_text', suggestion['text'])
                            if len(preview_text) > 100:
                                preview_text = preview_text[:100] + "..."
                            st.caption(f"💡 Suggested: {preview_text}")
                else:
                    # For other categories, just show checkbox
                    suggestion['selected'] = st.checkbox(
                        suggestion['text'],
                        value=default_value,
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


# Stage 5-7: Modification, Rescoring, Optimization Analysis
elif current_stage in ["modification", "rescoring", "optimization"]:
    st.header("Processing Resume Changes...")
    with st.spinner("Agents are working..."):
        if current_stage == "modification":
            st.info("Agent 2: Modifying your resume based on selected suggestions...")
        elif current_stage == "rescoring":
            st.info("Agent 3: Re-scoring the modified resume...")
        elif current_stage == "optimization":
            st.info("Agent 5: Analyzing optimization opportunities...")


# Stage 8: Optimization Suggestion Selection
elif current_stage == "awaiting_optimization_selection":
    state = st.session_state.workflow_state
    st.header("Step 3: Select Optimization Suggestions")

    # Display score info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Initial Score", f"{state['initial_score']}/100")

    with col2:
        improvement = state['score_improvement']
        st.metric(
            "New Score",
            f"{state['new_score']}/100",
            delta=f"+{improvement}" if improvement > 0 else str(improvement)
        )

    with col3:
        current_words = state.get('word_count_before_optimization', 0)
        target_words = 600
        if current_words <= target_words:
            st.success(f"✅ {current_words} words")
        else:
            st.warning(f"⚠️ {current_words} words (target: {target_words})")

    st.divider()

    # Display optimization analysis
    if state.get('optimization_analysis'):
        st.subheader("Optimization Analysis")
        st.info(state['optimization_analysis'])

    st.divider()

    # Suggestions with checkboxes
    st.subheader("Optimization Suggestions")
    st.markdown("Select the optimizations you want to apply to make your resume more concise:")

    # Group suggestions by category
    optimization_suggestions = state.get('optimization_suggestions', [])

    # Debug mode (set via environment variable DEBUG_MODE=1)
    import os
    debug_mode = os.getenv('DEBUG_MODE', '0') == '1'

    if debug_mode:
        print(f"[UI DEBUG] Found {len(optimization_suggestions)} optimization suggestions in state")
        if len(optimization_suggestions) > 0:
            print(f"[UI DEBUG] First suggestion: {optimization_suggestions[0]}")

    categories = {}
    for suggestion in optimization_suggestions:
        category = suggestion.get('category', 'Unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(suggestion)

    if debug_mode:
        print(f"[UI DEBUG] Grouped into {len(categories)} categories: {list(categories.keys())}")
        print(f"[UI DEBUG] Category counts: {[(cat, len(suggs)) for cat, suggs in categories.items()]}")

    # Display suggestions by category
    for category, suggestions in categories.items():
        if debug_mode:
            print(f"[UI DEBUG] Rendering category '{category}' with {len(suggestions)} suggestions")
        with st.expander(f"📌 {category} ({len(suggestions)} suggestions)", expanded=True):
            # Add Select All checkbox for this category
            select_all_key = f"select_all_opt_{category.replace(' ', '_')}"

            # Use checkbox with key - don't set value if using key
            select_all = st.checkbox(
                "✅ Select All",
                value=True,  # Default to selected for optimizations
                key=select_all_key
            )

            st.divider()

            for suggestion in suggestions:
                # Use Select All state if checked, otherwise use suggestion's default
                default_value = select_all if select_all else suggestion.get('selected', True)

                # Display suggestion with location context
                suggestion_label = suggestion['text']
                if suggestion.get('location'):
                    suggestion_label += f" (Location: {suggestion['location']})"

                suggestion['selected'] = st.checkbox(
                    suggestion_label,
                    value=default_value,
                    key=f"opt_suggestion_{suggestion['id']}"
                )

    st.divider()

    # Show estimated word reduction
    selected_count = sum(1 for s in state.get('optimization_suggestions', []) if s.get('selected', False))
    if selected_count > 0:
        st.info(f"✓ {selected_count} optimization(s) selected")
    else:
        st.warning("No optimizations selected. Resume will proceed to validation unchanged.")

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅️ Back to Suggestions", use_container_width=True):
            st.session_state.workflow_state['current_stage'] = "awaiting_selection"
            st.rerun()

    with col2:
        if st.button("⏭️ Skip Optimizations", use_container_width=True):
            # Deselect all and continue
            for suggestion in state.get('optimization_suggestions', []):
                suggestion['selected'] = False
            st.session_state.workflow_state['optimization_suggestions'] = state['optimization_suggestions']

            with st.spinner("Proceeding to validation..."):
                try:
                    updated_state = st.session_state.customizer.orchestrator.apply_optimizations(
                        st.session_state.workflow_state
                    )
                    st.session_state.workflow_state = updated_state
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.code(traceback.format_exc())

    with col3:
        if st.button("➡️ Apply Optimizations", type="primary", use_container_width=True):
            with st.spinner("Applying optimizations..."):
                try:
                    # Update state with current selections
                    st.session_state.workflow_state['optimization_suggestions'] = state['optimization_suggestions']

                    # Continue workflow
                    updated_state = st.session_state.customizer.orchestrator.apply_optimizations(
                        st.session_state.workflow_state
                    )
                    st.session_state.workflow_state = updated_state
                    st.rerun()
                except Exception as e:
                    st.error(f"Error applying optimizations: {str(e)}")
                    st.code(traceback.format_exc())


# Stage 9-10: Applying Optimizations Round 1, Round 2 Analysis
elif current_stage in ["applying_optimizations", "optimization_round2"]:
    st.header("Processing Optimizations...")
    with st.spinner("Agents are working..."):
        if current_stage == "applying_optimizations":
            st.info("Agent 5 (Round 1): Applying selected optimizations...")
        elif current_stage == "optimization_round2":
            st.info("Agent 5 (Round 2): Analyzing additional optimization opportunities...")


# Stage 11: Round 2 Optimization Suggestion Selection
elif current_stage == "awaiting_optimization_selection_round2":
    state = st.session_state.workflow_state
    st.header("Step 4: Select Additional Optimizations (Round 2)")

    st.info("💡 After applying Round 1 optimizations, Agent 5 has identified additional opportunities to make your resume even more concise.")

    # Display word count info
    col1, col2, col3 = st.columns(3)

    with col1:
        before_r1 = state.get('word_count_before', 0)
        st.metric("Before Round 1", f"{before_r1} words")

    with col2:
        after_r1 = state.get('word_count_after', 0)
        removed_r1 = state.get('words_removed', 0)
        st.metric(
            "After Round 1",
            f"{after_r1} words",
            delta=f"-{removed_r1}" if removed_r1 > 0 else "No change",
            delta_color="inverse"
        )

    with col3:
        target_words = 600
        if after_r1 <= target_words:
            st.success(f"✅ {after_r1} words (target: {target_words})")
        else:
            st.warning(f"⚠️ {after_r1} words (target: {target_words})")

    st.divider()

    # Display round 2 analysis
    if state.get('optimization_analysis_round2'):
        st.subheader("Round 2 Analysis")
        st.info(state['optimization_analysis_round2'])

    st.divider()

    # Suggestions with checkboxes
    st.subheader("Additional Optimization Suggestions")
    st.markdown("Select additional optimizations to make your resume even more concise:")

    # Group suggestions by category
    optimization_suggestions_r2 = state.get('optimization_suggestions_round2', [])

    if len(optimization_suggestions_r2) == 0:
        st.success("✅ No additional optimizations suggested! Your resume is well-optimized.")
        st.info("Click 'Skip Round 2' to proceed to validation.")
    else:
        categories = {}
        for suggestion in optimization_suggestions_r2:
            category = suggestion.get('category', 'Unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(suggestion)

        # Display suggestions by category
        for category, suggestions in categories.items():
            with st.expander(f"📌 {category} ({len(suggestions)} suggestions)", expanded=True):
                # Add Select All checkbox for this category
                select_all_key = f"select_all_opt_r2_{category.replace(' ', '_')}"

                select_all = st.checkbox(
                    "✅ Select All",
                    value=True,  # Default to selected
                    key=select_all_key
                )

                st.divider()

                for suggestion in suggestions:
                    # Use Select All state if checked, otherwise use suggestion's default
                    default_value = select_all if select_all else suggestion.get('selected', True)

                    # Display suggestion with location context
                    suggestion_label = suggestion['text']
                    if suggestion.get('location'):
                        suggestion_label += f" (Location: {suggestion['location']})"

                    suggestion['selected'] = st.checkbox(
                        suggestion_label,
                        value=default_value,
                        key=f"opt_r2_suggestion_{suggestion['id']}"
                    )

        st.divider()

        # Show estimated selections
        selected_count = sum(1 for s in state.get('optimization_suggestions_round2', []) if s.get('selected', False))
        if selected_count > 0:
            st.info(f"✓ {selected_count} optimization(s) selected for Round 2")
        else:
            st.warning("No Round 2 optimizations selected.")

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅️ Back to Round 1", use_container_width=True):
            st.session_state.workflow_state['current_stage'] = "awaiting_optimization_selection"
            st.rerun()

    with col2:
        if st.button("⏭️ Skip Round 2", use_container_width=True):
            # Deselect all Round 2 and continue
            for suggestion in state.get('optimization_suggestions_round2', []):
                suggestion['selected'] = False
            st.session_state.workflow_state['optimization_suggestions_round2'] = state['optimization_suggestions_round2']

            with st.spinner("Proceeding to validation..."):
                try:
                    updated_state = st.session_state.customizer.orchestrator.apply_optimizations_round2(
                        st.session_state.workflow_state
                    )
                    st.session_state.workflow_state = updated_state
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.code(traceback.format_exc())

    with col3:
        if st.button("➡️ Apply Round 2 Optimizations", type="primary", use_container_width=True):
            with st.spinner("Applying Round 2 optimizations..."):
                try:
                    # Update state with current selections
                    st.session_state.workflow_state['optimization_suggestions_round2'] = state['optimization_suggestions_round2']

                    # Continue workflow
                    updated_state = st.session_state.customizer.orchestrator.apply_optimizations_round2(
                        st.session_state.workflow_state
                    )
                    st.session_state.workflow_state = updated_state
                    st.rerun()
                except Exception as e:
                    st.error(f"Error applying Round 2 optimizations: {str(e)}")
                    st.code(traceback.format_exc())


# Stage 12-13: Applying Round 2 Optimizations, Validation
elif current_stage in ["applying_optimizations_round2", "validation"]:
    st.header("Finalizing Resume...")
    with st.spinner("Agents are working..."):
        if current_stage == "applying_optimizations_round2":
            st.info("Agent 5 (Round 2): Applying selected optimizations...")
        elif current_stage == "validation":
            st.info("Agent 4: Validating formatting and consistency...")


# Stage 14: Review Optimized Resume
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
            f"{state['new_score']}/100",
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

        # Determine which resume version to use
        has_round2 = state.get('optimized_resume_round2') is not None
        final_word_count = state.get('word_count_after_round2') if has_round2 else state.get('word_count_after', 0)

        # Show word count progression
        if has_round2:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Words Before", state.get('word_count_before', 'N/A'))

            with col2:
                r1_removed = state.get('words_removed', 0)
                st.metric(
                    "After Round 1",
                    state.get('word_count_after', 'N/A'),
                    delta=f"-{r1_removed}" if r1_removed > 0 else "No change",
                    delta_color="inverse"
                )

            with col3:
                r2_removed = state.get('words_removed_round2', 0)
                st.metric(
                    "After Round 2",
                    final_word_count,
                    delta=f"-{r2_removed}" if r2_removed > 0 else "No change",
                    delta_color="inverse"
                )

            with col4:
                word_target = 600
                if final_word_count <= word_target:
                    st.success(f"✅ Within Target")
                else:
                    st.warning(f"⚠️ Above Target")
                st.caption(f"Target: {word_target} words")

        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Words Before", state.get('word_count_before', 'N/A'))

            with col2:
                st.metric(
                    "Words After",
                    state.get('word_count_after', 'N/A'),
                    delta=f"-{state.get('words_removed', 0)}"
                )

            with col3:
                word_target = 600
                current_words = state.get('word_count_after', 0)
                if current_words <= word_target:
                    st.success(f"✅ Within Target ({word_target} words)")
                else:
                    st.warning(f"⚠️ Above Target ({word_target} words)")

        if state.get('optimization_summary'):
            with st.expander("Optimization Summary (Round 1)"):
                st.info(state['optimization_summary'])

        if state.get('optimization_changes'):
            with st.expander("Changes Made (Round 1)"):
                for change in state['optimization_changes']:
                    st.markdown(f"- {change}")

        if has_round2 and state.get('words_removed_round2', 0) > 0:
            with st.expander("Round 2 Optimizations"):
                st.info(f"Applied {state.get('words_removed_round2', 0)} additional word reductions")

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
            # Use the most recent version
            final_resume = (
                state.get('optimized_resume_round2') or
                state.get('optimized_resume') or
                state['modified_resume']
            )
            st.markdown(final_resume)

    st.divider()

    # Display validation results if available
    if state.get('validation_score'):
        st.subheader("Validation Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Validation Score",
                f"{state['validation_score']}/100",
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

                # Add Select All checkbox
                if 'select_all_validation' not in st.session_state:
                    st.session_state.select_all_validation = False

                select_all_validation = st.checkbox(
                    "✅ Select All",
                    value=st.session_state.select_all_validation,
                    key="select_all_validation"
                )

                st.divider()

                selected_recs = []
                for idx, rec in enumerate(state['validation_recommendations']):
                    # Use Select All state if checked, otherwise default to unchecked
                    default_value = select_all_validation if select_all_validation else False
                    is_selected = st.checkbox(
                        rec,
                        value=default_value,
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
        if st.button("➡️ Continue to Final Edits", type="primary", use_container_width=True):
            # Move to freeform editing stage
            st.session_state.workflow_state['current_stage'] = "freeform_editing"
            st.rerun()


# Stage 10: Freeform Editing (Optional)
elif current_stage == "freeform_editing":
    state = st.session_state.workflow_state
    st.header("Step 4: Final Edits (Optional)")

    st.info("💡 Request any additional changes before finalizing. Type your requested changes below, or click 'Finalize' to proceed to scoring.")

    # Initialize freeform changes history if not exists
    if state.get('freeform_changes_history') is None:
        state['freeform_changes_history'] = []

    # Get the current resume (use freeform if available, otherwise most recent version)
    current_resume = (
        state.get('freeform_resume') or
        state.get('optimized_resume_round2') or
        state.get('optimized_resume') or
        state['modified_resume']
    )

    # Display current resume
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Current Resume")
        with st.container():
            st.markdown("""
            <style>
            .freeform-preview {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                background-color: #f9f9f9;
                max-height: 500px;
                overflow-y: auto;
            }
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f'<div class="freeform-preview">', unsafe_allow_html=True)
            st.markdown(current_resume)
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Request Changes")

        # Text area for user input
        user_request = st.text_area(
            "Describe the changes you'd like:",
            height=150,
            placeholder="Example: Change the summary to emphasize leadership skills, or remove the last bullet point from Experience section, etc.",
            key="freeform_input"
        )

        if st.button("✨ Apply Changes", type="primary", use_container_width=True):
            if user_request.strip():
                with st.spinner("Applying your requested changes..."):
                    try:
                        from agents.agent_6_freeform import FreeformEditorAgent

                        agent = FreeformEditorAgent()
                        result = agent.apply_changes(
                            current_resume,
                            user_request,
                            state['job_description']
                        )

                        # Update state with new resume
                        state['freeform_resume'] = result['modified_resume']

                        # Add to change history
                        if state['freeform_changes_history'] is None:
                            state['freeform_changes_history'] = []
                        state['freeform_changes_history'].append({
                            'request': user_request,
                            'summary': result['changes_summary']
                        })

                        st.success(f"✅ Changes applied! {result['changes_summary']}")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error applying changes: {str(e)}")
                        st.code(traceback.format_exc())
            else:
                st.warning("Please enter your requested changes.")

        st.divider()

        # Show change history
        if state.get('freeform_changes_history'):
            st.subheader("Change History")
            for idx, change in enumerate(state['freeform_changes_history'], 1):
                with st.expander(f"Change #{idx}: {change['summary'][:50]}..."):
                    st.markdown(f"**Your Request:** {change['request']}")
                    st.markdown(f"**Changes Made:** {change['summary']}")

    st.divider()

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅️ Back to Review", use_container_width=True):
            st.session_state.workflow_state['current_stage'] = "awaiting_approval"
            st.rerun()

    with col2:
        if st.button("🔄 Reset to Optimized", use_container_width=True):
            # Reset to optimized version
            state['freeform_resume'] = None
            state['freeform_changes_history'] = []
            st.success("Reset to optimized version")
            st.rerun()

    with col3:
        if st.button("✅ Finalize & Score", type="primary", use_container_width=True):
            # Move to final scoring
            st.session_state.workflow_state['current_stage'] = "final_scoring"
            st.rerun()


# Stage 11: Final Scoring
elif current_stage == "final_scoring":
    state = st.session_state.workflow_state
    st.header("Step 5: Final Score")

    with st.spinner("Calculating final score..."):
        try:
            from agents.agent_1_scorer import ResumeScorerAgent

            # Get the final resume (most recent version)
            final_resume = (
                state.get('freeform_resume') or
                state.get('optimized_resume_round2') or
                state.get('optimized_resume') or
                state['modified_resume']
            )

            # Calculate final score
            agent = ResumeScorerAgent()
            result = agent.score_only(
                final_resume,
                state['job_description']
            )

            # Store final score
            final_score = result['score']
            state['final_score'] = final_score
            state['freeform_resume'] = final_resume  # Ensure this is saved

            # Display results
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Initial Score", f"{state['initial_score']}/100")

            with col2:
                st.metric("After Optimization", f"{state['new_score']}/100")

            with col3:
                improvement = final_score - state['initial_score']
                st.metric(
                    "Final Score",
                    f"{final_score}/10",
                    delta=f"+{improvement}" if improvement > 0 else str(improvement)
                )

            st.divider()

            if result.get('analysis'):
                st.subheader("Final Assessment")
                with st.expander("View Analysis", expanded=True):
                    st.markdown(result['analysis'])

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                if st.button("⬅️ Back to Edits", use_container_width=True):
                    st.session_state.workflow_state['current_stage'] = "freeform_editing"
                    st.rerun()

            with col2:
                if st.button("📄 Export Resume", type="primary", use_container_width=True):
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

        except Exception as e:
            st.error(f"Error calculating final score: {str(e)}")
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
            f"{state['validation_score']}/100",
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


# Stage 12-13: Export & Completed
elif current_stage in ["export", "completed"]:
    state = st.session_state.workflow_state
    st.header("Step 6: Export Complete!")

    st.success("Resume approved and exported successfully!")

    # Display final resume
    with st.expander("View Final Resume", expanded=True):
        final_resume = (
            state.get('freeform_resume') or
            state.get('optimized_resume_round2') or
            state.get('optimized_resume') or
            state['modified_resume']
        )
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

    # PDF Formatting Controls
    st.markdown("#### PDF Formatting")
    st.caption("Adjust these settings to fit your resume on one page. Decrease values to fit more content.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        font_size = st.slider(
            "Font Size (px)",
            min_value=7.0,
            max_value=12.0,
            value=st.session_state.workflow_state.get('pdf_font_size', 9.5),
            step=0.1,
            key="pdf_font_size_slider",
            help="Smaller font = more content per page. Default: 9.5px"
        )

    with col2:
        line_height = st.slider(
            "Line Height (em)",
            min_value=1.0,
            max_value=1.5,
            value=st.session_state.workflow_state.get('pdf_line_height', 1.2),
            step=0.05,
            key="pdf_line_height_slider",
            help="Smaller line height = tighter spacing. Default: 1.2em"
        )

    with col3:
        page_margin = st.slider(
            "Page Margin (in)",
            min_value=0.3,
            max_value=1.0,
            value=st.session_state.workflow_state.get('pdf_page_margin', 0.75),
            step=0.05,
            key="pdf_page_margin_slider",
            help="Smaller margin = more vertical space per page. Default: 0.75in"
        )

    with col4:
        if st.button("🔄 Regenerate PDF", use_container_width=True, help="Apply formatting changes and regenerate PDF"):
            with st.spinner("Regenerating PDF with new settings..."):
                try:
                    # Debug: Show what values we're using
                    print(f"\n{'='*60}")
                    print(f"[UI] REGENERATE PDF CLICKED")
                    print(f"[UI] Slider values: font_size={font_size}, line_height={line_height}, page_margin={page_margin}")
                    print(f"[UI] Before update - State contains: pdf_font_size={st.session_state.workflow_state.get('pdf_font_size')}, pdf_line_height={st.session_state.workflow_state.get('pdf_line_height')}, pdf_page_margin={st.session_state.workflow_state.get('pdf_page_margin')}")

                    # Update state with new formatting options
                    st.session_state.workflow_state['pdf_font_size'] = font_size
                    st.session_state.workflow_state['pdf_line_height'] = line_height
                    st.session_state.workflow_state['pdf_page_margin'] = page_margin

                    print(f"[UI] After update - State contains: pdf_font_size={st.session_state.workflow_state.get('pdf_font_size')}, pdf_line_height={st.session_state.workflow_state.get('pdf_line_height')}, pdf_page_margin={st.session_state.workflow_state.get('pdf_page_margin')}")
                    print(f"[UI] Calling orchestrator.export_resume()...")
                    print(f"{'='*60}\n")

                    # Re-export with new settings
                    updated_state = st.session_state.customizer.orchestrator.export_resume(
                        st.session_state.workflow_state
                    )
                    st.session_state.workflow_state = updated_state
                    st.success(f"PDF regenerated! Font: {font_size}px, Line height: {line_height}em, Margin: {page_margin}in")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error regenerating PDF: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

    st.divider()

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
        final_resume = (
            state.get('freeform_resume') or
            state.get('optimized_resume_round2') or
            state.get('optimized_resume') or
            state['modified_resume']
        )
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
        st.metric("Original Score", f"{state['initial_score']}/100")

    with col2:
        st.metric("Final Score", f"{state['new_score']}/100")

    with col3:
        improvement = state['score_improvement']
        st.metric("Improvement", f"+{improvement}" if improvement > 0 else str(improvement))

    st.divider()

    # Cover Letter Section (Optional)
    st.subheader("📨 Cover Letter (Optional)")
    st.markdown("Generate a tailored cover letter for this job application.")

    # Check if cover letter was already generated
    if state.get('cover_letter'):
        # Check if we have PDF (fully approved and exported)
        if state.get('cover_letter_pdf_bytes'):
            st.success("✅ Cover letter finalized!")

            # Display cover letter
            with st.expander("View Final Cover Letter", expanded=True):
                st.markdown(state['cover_letter'])

            # Download cover letter PDF
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📄 Download Cover Letter PDF",
                    data=state['cover_letter_pdf_bytes'],
                    file_name="cover_letter.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    label="📝 Download Cover Letter Markdown",
                    data=state['cover_letter'],
                    file_name="cover_letter.md",
                    mime="text/markdown",
                    use_container_width=True
                )

        else:
            # Cover letter generated and reviewed, but not yet exported
            st.success("✅ Cover letter generated and reviewed!")

            # Display the cover letter
            with st.expander("View Cover Letter", expanded=True):
                st.markdown(state['cover_letter'])

            # Show summary
            if state.get('cover_letter_summary'):
                with st.expander("Cover Letter Approach"):
                    st.info(state['cover_letter_summary'])

            # Display review feedback from Agent 8
            if state.get('cover_letter_review'):
                st.subheader("🔍 Review Feedback")
                review = state['cover_letter_review']

                # Overall assessment
                st.info(f"**Overall Assessment:** {review.get('overall_assessment', 'N/A')}")

                # Revision status
                revision_needed = review.get('revision_needed', False)
                revision_priority = review.get('revision_priority', 'none')

                if revision_needed:
                    if revision_priority == "critical":
                        st.error(f"⚠️ Revision Priority: {revision_priority.upper()}")
                    elif revision_priority == "moderate":
                        st.warning(f"⚠️ Revision Priority: {revision_priority.capitalize()}")
                    else:
                        st.info(f"ℹ️ Revision Priority: {revision_priority.capitalize()}")
                else:
                    st.success("✅ No critical revisions needed!")

                # Show issues
                col1, col2, col3 = st.columns(3)

                with col1:
                    critical_issues = review.get('critical_issues', [])
                    if critical_issues:
                        with st.expander(f"🔴 Critical Issues ({len(critical_issues)})", expanded=True):
                            for i, issue in enumerate(critical_issues, 1):
                                st.markdown(f"**{i}. {issue.get('issue', 'N/A')}**")
                                st.markdown(f"📍 *Location:* {issue.get('location', 'N/A')}")
                                st.markdown(f"🔧 *Fix:* {issue.get('fix', 'N/A')}")
                                st.divider()

                with col2:
                    content_issues = review.get('content_issues', [])
                    if content_issues:
                        with st.expander(f"🟡 Content Issues ({len(content_issues)})", expanded=False):
                            for i, issue in enumerate(content_issues, 1):
                                st.markdown(f"**{i}. {issue.get('issue', 'N/A')}**")
                                st.markdown(f"📍 *Location:* {issue.get('location', 'N/A')}")
                                st.markdown(f"🔧 *Fix:* {issue.get('fix', 'N/A')}")
                                st.divider()

                with col3:
                    minor_issues = review.get('minor_issues', [])
                    if minor_issues:
                        with st.expander(f"🔵 Minor Issues ({len(minor_issues)})", expanded=False):
                            for i, issue in enumerate(minor_issues, 1):
                                st.markdown(f"**{i}. {issue.get('issue', 'N/A')}**")
                                st.markdown(f"📍 *Location:* {issue.get('location', 'N/A')}")
                                st.markdown(f"🔧 *Fix:* {issue.get('fix', 'N/A')}")
                                st.divider()

                # Show strengths
                strengths = review.get('strengths', [])
                if strengths:
                    with st.expander("💪 Strengths", expanded=False):
                        for strength in strengths:
                            st.markdown(f"✓ {strength}")

            # Show revision notes if this is a revised version
            if state.get('cover_letter_revision_notes'):
                with st.expander("📝 Revision Notes"):
                    st.markdown(state['cover_letter_revision_notes'])

            st.divider()

            # User feedback and actions
            st.subheader("📝 Your Feedback (Optional)")
            user_feedback = st.text_area(
                "Add any additional feedback or changes you'd like:",
                placeholder="e.g., 'Make the tone more formal' or 'Emphasize my leadership experience'",
                height=100,
                key="cover_letter_user_feedback"
            )

            # Action buttons
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔄 Revise Cover Letter", use_container_width=True):
                    with st.spinner("Revising cover letter based on feedback..."):
                        try:
                            # Revise cover letter using orchestrator
                            updated_state = st.session_state.customizer.orchestrator.revise_cover_letter(
                                st.session_state.workflow_state,
                                user_feedback=user_feedback if user_feedback.strip() else None
                            )
                            st.session_state.workflow_state = updated_state
                            st.success("Cover letter revised successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error revising cover letter: {str(e)}")
                            st.code(traceback.format_exc())

            with col2:
                if st.button("✅ Approve & Export PDF", type="primary", use_container_width=True):
                    with st.spinner("Exporting cover letter to PDF..."):
                        try:
                            # Export cover letter using orchestrator
                            updated_state = st.session_state.customizer.orchestrator.export_cover_letter(
                                st.session_state.workflow_state
                            )
                            st.session_state.workflow_state = updated_state
                            st.success("Cover letter exported successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error exporting cover letter: {str(e)}")
                            st.code(traceback.format_exc())

    else:
        # Offer to generate cover letter
        st.info("💡 Click below to generate a personalized cover letter based on your resume and the job description.")

        if st.button("✨ Generate Cover Letter", use_container_width=True):
            with st.spinner("Generating and reviewing cover letter..."):
                try:
                    # Generate cover letter using orchestrator (includes review)
                    updated_state = st.session_state.customizer.orchestrator.generate_cover_letter(
                        st.session_state.workflow_state
                    )
                    st.session_state.workflow_state = updated_state
                    st.success("Cover letter generated and reviewed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating cover letter: {str(e)}")
                    st.code(traceback.format_exc())

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
