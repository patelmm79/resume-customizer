"""Node functions for LangGraph workflow."""
from typing import Dict, Any
from workflow.state import WorkflowState
from agents.agent_1_scorer import ResumeScorerAgent
from agents.agent_2_modifier import ResumeModifierAgent
from agents.agent_4_validator import ResumeValidatorAgent
from agents.agent_5_optimizer import ResumeOptimizerAgent
from agents.agent_7_cover_letter import CoverLetterAgent
from agents.agent_8_reviewer import review_cover_letter
from utils.job_scraper import JobScraper
from utils.pdf_exporter import PDFExporter


def fetch_job_description_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Fetch job description from URL if provided.

    Args:
        state: Current workflow state

    Returns:
        Updated state with job description
    """
    if state.get("job_url") and not state.get("job_description"):
        try:
            scraper = JobScraper()
            job_desc = scraper.fetch_job_description(state["job_url"])
            return {
                "job_description": job_desc,
                "current_stage": "scoring",
                "messages": [{"role": "system", "content": "Job description fetched successfully"}]
            }
        except Exception as e:
            return {
                "error": f"Failed to fetch job description: {str(e)}",
                "current_stage": "error",
                "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
            }

    return {
        "current_stage": "scoring",
        "messages": [{"role": "system", "content": "Using provided job description"}]
    }


def scoring_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 1: Score and analyze resume.

    Args:
        state: Current workflow state

    Returns:
        Updated state with scoring results
    """
    try:
        agent = ResumeScorerAgent()
        result = agent.analyze_and_score(
            state["original_resume"],
            state["job_description"]
        )

        return {
            "initial_score": result["score"],
            "analysis": result["analysis"],
            "suggestions": result["suggestions"],
            "current_stage": "awaiting_selection",
            "messages": [{"role": "ai", "content": f"Agent 1: Initial score: {result['score']}/10"}]
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Scoring failed with full traceback:\n{error_details}")
        return {
            "error": f"Scoring failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def modification_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 2: Modify resume based on suggestions.

    Args:
        state: Current workflow state

    Returns:
        Updated state with modified resume and analysis
    """
    try:
        agent = ResumeModifierAgent()
        modified = agent.modify_resume(
            state["original_resume"],
            state["suggestions"],
            state["job_description"]
        )

        # Get analysis of what was modified
        modification_analysis = agent.get_modification_analysis(state["suggestions"])

        return {
            "modified_resume": modified,
            "modification_analysis": modification_analysis,
            "current_stage": "rescoring",
            "messages": [{"role": "ai", "content": "Agent 2: Resume modified successfully"}]
        }
    except Exception as e:
        return {
            "error": f"Modification failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def rescoring_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 1 (Rescoring): Score modified resume.

    Args:
        state: Current workflow state

    Returns:
        Updated state with rescoring results
    """
    try:
        agent = ResumeScorerAgent()
        result = agent.score_only(
            state["modified_resume"],
            state["job_description"]
        )

        new_score = result["score"]
        score_improvement = new_score - state["initial_score"]

        return {
            "new_score": new_score,
            "score_improvement": score_improvement,
            "comparison": result["analysis"],
            "improvements": [],  # Not needed for simple rescoring
            "concerns": [],
            "recommendation": "Ready to Optimize" if new_score >= state["initial_score"] else "Consider More Changes",
            "reasoning": result["analysis"],
            "current_stage": "optimization",
            "messages": [{"role": "ai", "content": f"Agent 1 (Rescoring): New score: {new_score}/100 (improvement: +{score_improvement})"}]
        }
    except Exception as e:
        return {
            "error": f"Rescoring failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def optimization_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 5: Suggest optimization opportunities (does not auto-apply).

    Args:
        state: Current workflow state

    Returns:
        Updated state with optimization suggestions
    """
    try:
        # Check for debug mode
        import os
        debug_mode = os.getenv('DEBUG_MODE', '0') == '1'

        agent = ResumeOptimizerAgent(debug_mode=debug_mode)
        result = agent.suggest_optimizations(
            state["modified_resume"],
            state["job_description"],
            state["new_score"]
        )

        return {
            "optimization_suggestions": result["suggestions"],
            "optimization_analysis": result["analysis"],
            "word_count_before_optimization": result["current_word_count"],
            "current_stage": "awaiting_optimization_selection",
            "messages": [{
                "role": "ai",
                "content": f"Agent 5: Found {len(result['suggestions'])} optimization opportunities (current: {result['current_word_count']} words)"
            }]
        }
    except Exception as e:
        return {
            "error": f"Optimization analysis failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def apply_optimizations_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 5: Apply selected optimization suggestions.

    Args:
        state: Current workflow state with selected optimization suggestions

    Returns:
        Updated state with optimized resume
    """
    try:
        # Check for debug mode
        import os
        debug_mode = os.getenv('DEBUG_MODE', '0') == '1'

        agent = ResumeOptimizerAgent(debug_mode=debug_mode)

        # Get selected suggestions
        selected_suggestions = [
            s for s in state.get("optimization_suggestions", [])
            if s.get("selected", False)
        ]

        if not selected_suggestions:
            # No optimizations selected, skip to validation
            return {
                "optimized_resume": state["modified_resume"],
                "word_count_before": len(state["modified_resume"].split()),
                "word_count_after": len(state["modified_resume"].split()),
                "words_removed": 0,
                "optimization_summary": "No optimizations applied",
                "optimization_changes": [],
                "current_stage": "validation",
                "messages": [{"role": "ai", "content": "Agent 5: No optimizations selected, proceeding to validation"}]
            }

        # Apply selected optimizations
        optimized_resume = agent.apply_optimizations(
            state["modified_resume"],
            selected_suggestions,
            state["job_description"]
        )

        word_count_before = len(state["modified_resume"].split())
        word_count_after = len(optimized_resume.split())
        words_removed = word_count_before - word_count_after

        return {
            "optimized_resume": optimized_resume,
            "word_count_before": word_count_before,
            "word_count_after": word_count_after,
            "words_removed": words_removed,
            "optimization_summary": f"Applied {len(selected_suggestions)} optimization(s)",
            "optimization_changes": [s["text"] for s in selected_suggestions],
            "current_stage": "optimization_round2",
            "messages": [{
                "role": "ai",
                "content": f"Agent 5: Optimized resume from {word_count_before} to {word_count_after} words (-{words_removed} words)"
            }]
        }
    except Exception as e:
        return {
            "error": f"Optimization application failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def optimization_round2_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 5 Round 2: Suggest additional optimization opportunities after first round.

    Args:
        state: Current workflow state

    Returns:
        Updated state with second round optimization suggestions
    """
    try:
        # Check for debug mode
        import os
        debug_mode = os.getenv('DEBUG_MODE', '0') == '1'

        # Get previously applied suggestions to avoid repeating
        previous_suggestions = state.get("optimization_suggestions", [])
        previous_changes = [s["text"] for s in previous_suggestions if s.get("selected", False)]

        agent = ResumeOptimizerAgent(debug_mode=debug_mode)

        # Use optimized resume from round 1 as input
        resume_to_optimize = state.get("optimized_resume") or state["modified_resume"]

        result = agent.suggest_optimizations(
            resume_to_optimize,
            state["job_description"],
            state["new_score"]
        )

        # Filter out suggestions that are too similar to round 1
        filtered_suggestions = []
        for suggestion in result["suggestions"]:
            # Simple check: if suggestion text doesn't closely match any previous change
            is_duplicate = any(
                suggestion["text"].lower() in prev.lower() or prev.lower() in suggestion["text"].lower()
                for prev in previous_changes
            )
            if not is_duplicate:
                filtered_suggestions.append(suggestion)

        return {
            "optimization_suggestions_round2": filtered_suggestions,
            "optimization_analysis_round2": result["analysis"],
            "current_stage": "awaiting_optimization_selection_round2",
            "messages": [{
                "role": "ai",
                "content": f"Agent 5 (Round 2): Found {len(filtered_suggestions)} additional optimization opportunities"
            }]
        }
    except Exception as e:
        return {
            "error": f"Round 2 optimization analysis failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def apply_optimizations_round2_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 5 Round 2: Apply selected second round optimization suggestions.

    Args:
        state: Current workflow state with selected round 2 optimization suggestions

    Returns:
        Updated state with optimized resume from round 2
    """
    try:
        # Check for debug mode
        import os
        debug_mode = os.getenv('DEBUG_MODE', '0') == '1'

        agent = ResumeOptimizerAgent(debug_mode=debug_mode)

        # Get selected round 2 suggestions
        selected_suggestions = [
            s for s in state.get("optimization_suggestions_round2", [])
            if s.get("selected", False)
        ]

        resume_to_optimize = state.get("optimized_resume") or state["modified_resume"]

        if not selected_suggestions:
            # No round 2 optimizations selected, proceed to validation
            return {
                "optimized_resume_round2": resume_to_optimize,
                "word_count_after_round2": len(resume_to_optimize.split()),
                "words_removed_round2": 0,
                "current_stage": "validation",
                "messages": [{"role": "ai", "content": "Agent 5 (Round 2): No additional optimizations selected, proceeding to validation"}]
            }

        # Apply selected round 2 optimizations
        optimized_resume = agent.apply_optimizations(
            resume_to_optimize,
            selected_suggestions,
            state["job_description"]
        )

        word_count_before_r2 = len(resume_to_optimize.split())
        word_count_after_r2 = len(optimized_resume.split())
        words_removed_r2 = word_count_before_r2 - word_count_after_r2

        return {
            "optimized_resume_round2": optimized_resume,
            "word_count_after_round2": word_count_after_r2,
            "words_removed_round2": words_removed_r2,
            "current_stage": "validation",
            "messages": [{
                "role": "ai",
                "content": f"Agent 5 (Round 2): Further optimized resume from {word_count_before_r2} to {word_count_after_r2} words (-{words_removed_r2} words)"
            }]
        }
    except Exception as e:
        return {
            "error": f"Round 2 optimization application failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def validation_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 4: Validate resume formatting and consistency.

    Args:
        state: Current workflow state

    Returns:
        Updated state with validation results
    """
    try:
        agent = ResumeValidatorAgent()
        # Use the most recent version: round 2 > round 1 > modified
        resume_to_validate = (
            state.get("optimized_resume_round2") or
            state.get("optimized_resume") or
            state["modified_resume"]
        )
        result = agent.validate_resume(resume_to_validate)

        return {
            "validation_score": result["validation_score"],
            "is_valid": result["is_valid"],
            "validation_issues": result["issues"],
            "validation_recommendations": result["recommendations"],
            "validation_summary": result["summary"],
            "critical_count": result["critical_count"],
            "warning_count": result["warning_count"],
            "info_count": result["info_count"],
            "current_stage": "awaiting_approval",
            "messages": [{"role": "ai", "content": f"Agent 4: Validation score: {result['validation_score']}/100"}]
        }
    except Exception as e:
        return {
            "error": f"Validation failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def export_pdf_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Export resume to PDF.

    Args:
        state: Current workflow state

    Returns:
        Updated state with PDF output
    """
    try:
        exporter = PDFExporter()

        # Use the most recent version: freeform > round2 > round1 > modified > original
        final_resume = (
            state.get("freeform_resume") or
            state.get("optimized_resume_round2") or
            state.get("optimized_resume") or
            state.get("modified_resume") or
            state.get("original_resume")
        )

        # Get PDF formatting options from state (with defaults)
        font_size = state.get("pdf_font_size", 9.5)
        line_height = state.get("pdf_line_height", 1.2)
        page_margin = state.get("pdf_page_margin", 0.75)

        # DEBUG: Always print what we're using
        print(f"[export_pdf_node] Retrieved from state: font_size={font_size}, line_height={line_height}, page_margin={page_margin}")
        print(f"[export_pdf_node] State keys: {list(state.keys())}")

        # Generate PDF bytes for download
        pdf_bytes = exporter.markdown_to_pdf_bytes(
            final_resume,
            font_size=font_size,
            line_height=line_height,
            page_margin=page_margin
        )

        # Optionally save to file
        pdf_path = exporter.markdown_to_pdf(final_resume)

        return {
            "pdf_path": pdf_path,
            "pdf_bytes": pdf_bytes,
            "current_stage": "completed",
            "messages": [{"role": "system", "content": f"PDF exported: {pdf_path}"}]
        }
    except Exception as e:
        return {
            "error": f"PDF export failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def human_feedback_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Placeholder for human feedback/approval.

    This is a pass-through node. Actual approval happens
    via external state updates.

    Args:
        state: Current workflow state

    Returns:
        State with feedback recorded
    """
    return {
        "messages": [{"role": "system", "content": "Awaiting human feedback"}]
    }


def cover_letter_generation_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 7: Generate cover letter based on resume and job description.

    Args:
        state: Current workflow state

    Returns:
        Updated state with cover letter
    """
    try:
        agent = CoverLetterAgent()

        # Use freeform resume if available, otherwise optimized, otherwise modified
        final_resume = state.get("freeform_resume") or state.get("optimized_resume") or state.get("modified_resume")

        if not final_resume:
            raise ValueError("No resume found in state. Please complete the resume workflow first.")

        result = agent.generate_cover_letter(
            final_resume,
            state["job_description"]
        )

        # Validate the result
        cover_letter = result.get("cover_letter", "")
        if not cover_letter or not cover_letter.strip():
            raise ValueError("Cover letter generation returned empty content. Please try again.")

        return {
            "cover_letter": cover_letter,
            "cover_letter_summary": result.get("summary", "Cover letter generated successfully."),
            "current_stage": "cover_letter_ready",
            "messages": [{"role": "ai", "content": "Agent 7: Cover letter generated successfully"}]
        }
    except Exception as e:
        return {
            "error": f"Cover letter generation failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def export_cover_letter_pdf_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Export cover letter to PDF.

    Args:
        state: Current workflow state

    Returns:
        Updated state with cover letter PDF output
    """
    try:
        # Check if cover letter exists
        cover_letter = state.get("cover_letter")
        if not cover_letter:
            raise ValueError("No cover letter found in state. Generate cover letter first.")

        exporter = PDFExporter()

        # Get PDF formatting options from state (with defaults)
        font_size = state.get("cover_letter_pdf_font_size", 9.5)
        line_height = state.get("cover_letter_pdf_line_height", 1.2)
        page_margin = state.get("cover_letter_pdf_page_margin", 0.75)

        # Generate PDF bytes for download
        pdf_bytes = exporter.markdown_to_pdf_bytes(
            cover_letter,
            font_size=font_size,
            line_height=line_height,
            page_margin=page_margin
        )

        # Optionally save to file
        pdf_path = exporter.markdown_to_pdf(cover_letter, filename="cover_letter.pdf")

        return {
            "cover_letter_pdf_path": pdf_path,
            "cover_letter_pdf_bytes": pdf_bytes,
            "current_stage": "completed",
            "messages": [{"role": "system", "content": f"Cover letter PDF exported: {pdf_path}"}]
        }
    except Exception as e:
        return {
            "error": f"Cover letter PDF export failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def review_cover_letter_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 8: Review cover letter for quality and issues.

    Args:
        state: Current workflow state

    Returns:
        Updated state with review feedback
    """
    try:
        # Get the cover letter to review
        cover_letter = state.get("cover_letter")
        if not cover_letter:
            raise ValueError("No cover letter found to review")

        # Get resume for context
        final_resume = state.get("freeform_resume") or state.get("optimized_resume") or state.get("modified_resume")
        if not final_resume:
            raise ValueError("No resume found in state")

        # Review the cover letter
        review_result = review_cover_letter(
            cover_letter=cover_letter,
            job_description=state["job_description"],
            resume=final_resume
        )

        # Determine if revision is needed
        revision_needed = review_result.get("revision_needed", False)
        revision_priority = review_result.get("revision_priority", "none")

        return {
            "cover_letter_review": review_result,
            "cover_letter_revision_needed": revision_needed,
            "current_stage": "cover_letter_reviewed",
            "messages": [{
                "role": "ai",
                "content": f"Agent 8: Cover letter reviewed. Revision needed: {revision_needed} (Priority: {revision_priority})"
            }]
        }
    except Exception as e:
        return {
            "error": f"Cover letter review failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }


def revise_cover_letter_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Agent 7 (Revision): Revise cover letter based on reviewer feedback and user input.

    Args:
        state: Current workflow state

    Returns:
        Updated state with revised cover letter
    """
    try:
        # Get required data
        original_cover_letter = state.get("cover_letter")
        review_feedback = state.get("cover_letter_review")
        user_feedback = state.get("user_cover_letter_feedback", "")

        if not original_cover_letter:
            raise ValueError("No cover letter found to revise")

        if not review_feedback:
            raise ValueError("No review feedback found")

        # Get resume for context
        final_resume = state.get("freeform_resume") or state.get("optimized_resume") or state.get("modified_resume")
        if not final_resume:
            raise ValueError("No resume found in state")

        # Revise the cover letter
        agent = CoverLetterAgent()
        revision_result = agent.revise_cover_letter(
            original_cover_letter=original_cover_letter,
            reviewer_feedback=review_feedback,
            resume_content=final_resume,
            job_description=state["job_description"],
            user_feedback=user_feedback
        )

        return {
            "cover_letter_revised": revision_result["cover_letter"],
            "cover_letter_revision_notes": revision_result["revision_notes"],
            "cover_letter": revision_result["cover_letter"],  # Update main cover letter
            "current_stage": "cover_letter_revised",
            "messages": [{
                "role": "ai",
                "content": "Agent 7: Cover letter revised based on feedback"
            }]
        }
    except Exception as e:
        return {
            "error": f"Cover letter revision failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }
