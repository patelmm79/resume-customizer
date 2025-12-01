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

    # Agent 5 outputs (Optimization)
    optimization_suggestions: Optional[List[SuggestionDict]]  # Suggestions from Agent 5
    optimization_analysis: Optional[str]  # Analysis of optimization opportunities
    word_count_before_optimization: Optional[int]  # Word count before optimization
    optimized_resume: Optional[str]  # Resume after applying optimizations
    word_count_before: Optional[int]  # Word count before applying selected optimizations
    word_count_after: Optional[int]  # Word count after applying selected optimizations
    words_removed: Optional[int]  # Words removed by optimization
    optimization_summary: Optional[str]  # Summary of optimizations applied
    optimization_changes: Optional[List[str]]  # List of changes made

    # Agent 4 outputs (Validation)
    validation_score: Optional[int]
    is_valid: Optional[bool]
    validation_issues: Optional[List[Dict]]
    validation_recommendations: Optional[List[str]]
    validation_summary: Optional[str]
    critical_count: Optional[int]
    warning_count: Optional[int]
    info_count: Optional[int]

    # Agent 6 outputs (Freeform Editing)
    freeform_resume: Optional[str]
    freeform_changes_history: Optional[List[Dict]]
    final_score: Optional[int]

    # Agent 7 outputs (Cover Letter)
    cover_letter: Optional[str]
    cover_letter_summary: Optional[str]
    generate_cover_letter: Optional[bool]

    # Final outputs
    pdf_path: Optional[str]
    pdf_bytes: Optional[bytes]
    cover_letter_pdf_path: Optional[str]
    cover_letter_pdf_bytes: Optional[bytes]

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
        optimized_resume=None,
        word_count_before=None,
        word_count_after=None,
        words_removed=None,
        optimization_summary=None,
        optimization_changes=None,
        validation_score=None,
        is_valid=None,
        validation_issues=None,
        validation_recommendations=None,
        validation_summary=None,
        critical_count=None,
        warning_count=None,
        info_count=None,
        freeform_resume=None,
        freeform_changes_history=None,
        final_score=None,
        cover_letter=None,
        cover_letter_summary=None,
        generate_cover_letter=False,
        pdf_path=None,
        pdf_bytes=None,
        cover_letter_pdf_path=None,
        cover_letter_pdf_bytes=None,
        current_stage="fetch_job" if job_url else "scoring",
        approved=False,
        error=None,
        messages=[]
    )
