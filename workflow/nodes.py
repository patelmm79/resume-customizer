"""Node functions for LangGraph workflow."""
from typing import Dict, Any
from workflow.state import WorkflowState
from agents.agent_1_scorer import ResumeScorerAgent
from agents.agent_2_modifier import ResumeModifierAgent
from agents.agent_3_rescorer import ResumeRescorerAgent
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
    Agent 3: Rescore modified resume.

    Args:
        state: Current workflow state

    Returns:
        Updated state with rescoring results
    """
    try:
        agent = ResumeRescorerAgent()
        result = agent.rescore_resume(
            state["modified_resume"],
            state["job_description"],
            state["initial_score"]
        )

        return {
            "new_score": result["new_score"],
            "score_improvement": result["score_improvement"],
            "comparison": result["comparison"],
            "improvements": result["improvements"],
            "concerns": result["concerns"],
            "recommendation": result["recommendation"],
            "reasoning": result["reasoning"],
            "current_stage": "awaiting_approval",
            "messages": [{"role": "ai", "content": f"Agent 3: New score: {result['new_score']}/10 (improvement: +{result['score_improvement']})"}]
        }
    except Exception as e:
        return {
            "error": f"Rescoring failed: {str(e)}",
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

        # Generate PDF bytes for download
        pdf_bytes = exporter.markdown_to_pdf_bytes(state["modified_resume"])

        # Optionally save to file
        pdf_path = exporter.markdown_to_pdf(state["modified_resume"])

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
