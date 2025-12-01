"""Node functions for LangGraph workflow."""
from typing import Dict, Any
from workflow.state import WorkflowState
from agents.agent_1_scorer import ResumeScorerAgent
from agents.agent_2_modifier import ResumeModifierAgent
from agents.agent_4_validator import ResumeValidatorAgent
from agents.agent_5_optimizer import ResumeOptimizerAgent
from agents.agent_7_cover_letter import CoverLetterAgent
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
        Updated state with modified resume
    """
    try:
        agent = ResumeModifierAgent()
        modified = agent.modify_resume(
            state["original_resume"],
            state["suggestions"],
            state["job_description"]
        )

        return {
            "modified_resume": modified,
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
        agent = ResumeOptimizerAgent()
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
        agent = ResumeOptimizerAgent()

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
            "current_stage": "validation",
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
        # Use optimized resume if available, otherwise use modified resume
        resume_to_validate = state.get("optimized_resume") or state["modified_resume"]
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

        # Use freeform resume if available, otherwise optimized, otherwise modified
        final_resume = state.get("freeform_resume") or state.get("optimized_resume") or state["modified_resume"]

        # Generate PDF bytes for download
        pdf_bytes = exporter.markdown_to_pdf_bytes(final_resume)

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

        # Generate PDF bytes for download
        pdf_bytes = exporter.markdown_to_pdf_bytes(cover_letter)

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
