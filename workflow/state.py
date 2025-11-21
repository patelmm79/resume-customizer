"""State definitions for LangGraph workflow."""
from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph.message import add_messages


class SuggestionDict(TypedDict):
    """Structure for a single suggestion."""
    id: int
    text: str
    category: str
    selected: bool


class WorkflowState(TypedDict):
    """State for the resume customization workflow."""
    # Input data
    original_resume: str
    job_description: str
    job_url: Optional[str]

    # Agent 1 outputs
    initial_score: Optional[int]
    analysis: Optional[str]
    suggestions: Optional[List[SuggestionDict]]

    # Agent 2 outputs
    modified_resume: Optional[str]

    # Agent 3 outputs
    new_score: Optional[int]
    score_improvement: Optional[int]
    comparison: Optional[str]
    improvements: Optional[List[str]]
    concerns: Optional[List[str]]
    recommendation: Optional[str]
    reasoning: Optional[str]

    # Agent 4 outputs (Validation)
    validation_score: Optional[int]
    is_valid: Optional[bool]
    validation_issues: Optional[List[Dict]]
    validation_recommendations: Optional[List[str]]
    validation_summary: Optional[str]
    critical_count: Optional[int]
    warning_count: Optional[int]
    info_count: Optional[int]

    # Final outputs
    pdf_path: Optional[str]
    pdf_bytes: Optional[bytes]

    # Workflow control
    current_stage: str
    approved: bool
    error: Optional[str]
    messages: Annotated[List[Dict], add_messages]


def create_initial_state(
    resume: str,
    job_description: str = None,
    job_url: str = None
) -> WorkflowState:
    """
    Create initial workflow state.

    Args:
        resume: Original resume content
        job_description: Job description text
        job_url: Job posting URL

    Returns:
        Initial workflow state
    """
    return WorkflowState(
        original_resume=resume,
        job_description=job_description or "",
        job_url=job_url,
        initial_score=None,
        analysis=None,
        suggestions=None,
        modified_resume=None,
        new_score=None,
        score_improvement=None,
        comparison=None,
        improvements=None,
        concerns=None,
        recommendation=None,
        reasoning=None,
        validation_score=None,
        is_valid=None,
        validation_issues=None,
        validation_recommendations=None,
        validation_summary=None,
        critical_count=None,
        warning_count=None,
        info_count=None,
        pdf_path=None,
        pdf_bytes=None,
        current_stage="fetch_job" if job_url else "scoring",
        approved=False,
        error=None,
        messages=[]
    )
