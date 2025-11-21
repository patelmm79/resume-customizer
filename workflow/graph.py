"""LangGraph workflow definition for resume customization."""
from typing import Literal
from langgraph.graph import StateGraph, END
from workflow.state import WorkflowState
from workflow.nodes import (
    fetch_job_description_node,
    scoring_node,
    modification_node,
    rescoring_node,
    optimization_node,
    validation_node,
    export_pdf_node,
    human_feedback_node
)


def should_continue_to_modification(state: WorkflowState) -> Literal["modify", "end"]:
    """
    Route after scoring based on whether suggestions are selected.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    if state.get("error"):
        return "end"

    # Check if any suggestions are selected
    suggestions = state.get("suggestions", [])
    if any(s.get("selected", False) for s in suggestions):
        return "modify"

    return "end"


def should_continue_to_export(state: WorkflowState) -> Literal["export", "rescoring", "end"]:
    """
    Route after rescoring based on approval status.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    if state.get("error"):
        return "end"

    if state.get("approved"):
        return "export"

    # If not approved and user wants to try again, go back to scoring
    # This would be handled by external workflow restart
    return "end"


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for resume customization.

    Workflow stages:
    1. fetch_job (optional) - Fetch job description from URL
    2. scoring - Agent 1 scores and suggests improvements
    3. [Human selects suggestions]
    4. modification - Agent 2 modifies resume
    5. rescoring - Agent 3 rescores and evaluates
    6. optimization - Agent 5 optimizes resume length
    7. validation - Agent 4 validates formatting and consistency
    8. [Human approves]
    9. export - Generate PDF

    Returns:
        Compiled LangGraph workflow
    """
    # Create the graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("fetch_job", fetch_job_description_node)
    workflow.add_node("scoring", scoring_node)
    workflow.add_node("modify", modification_node)
    workflow.add_node("rescoring", rescoring_node)
    workflow.add_node("export", export_pdf_node)

    # Define edges
    # Start -> fetch_job (if URL provided) OR scoring (if description provided)
    workflow.set_conditional_entry_point(
        lambda state: "fetch_job" if state.get("job_url") else "scoring"
    )

    # fetch_job -> scoring
    workflow.add_edge("fetch_job", "scoring")

    # scoring -> END (waits for human to select suggestions)
    # In practice, we'll invoke the workflow again with updated state
    workflow.add_edge("scoring", END)

    # For continuing after human selection:
    # This is done by creating a new invocation starting from modify node

    return workflow


def create_modification_workflow() -> StateGraph:
    """
    Create workflow for modification phase (after suggestion selection).

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(WorkflowState)

    workflow.add_node("modify", modification_node)
    workflow.add_node("rescoring", rescoring_node)
    workflow.add_node("optimization", optimization_node)
    workflow.add_node("validation", validation_node)

    workflow.set_entry_point("modify")
    workflow.add_edge("modify", "rescoring")
    workflow.add_edge("rescoring", "optimization")
    workflow.add_edge("optimization", "validation")
    workflow.add_edge("validation", END)

    return workflow


def create_export_workflow() -> StateGraph:
    """
    Create workflow for export phase (after approval).

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(WorkflowState)

    workflow.add_node("export", export_pdf_node)

    workflow.set_entry_point("export")
    workflow.add_edge("export", END)

    return workflow


# Compile workflows
analysis_workflow = create_workflow().compile()
modification_workflow = create_modification_workflow().compile()
export_workflow = create_export_workflow().compile()
