"""Orchestrator for LangGraph workflow."""
from typing import Dict, Any, Optional
from workflow.state import WorkflowState, create_initial_state
from workflow.graph import (
    analysis_workflow,
    modification_workflow,
    export_workflow
)


class ResumeWorkflowOrchestrator:
    """
    Orchestrator for the resume customization workflow using LangGraph.

    This class provides a clean interface for executing the multi-stage
    workflow with human-in-the-loop interactions.
    """

    def __init__(self):
        """Initialize the orchestrator with compiled workflows."""
        self.analysis_workflow = analysis_workflow
        self.modification_workflow = modification_workflow
        self.export_workflow = export_workflow

    def start_analysis(
        self,
        resume: str,
        job_description: str = None,
        job_url: str = None
    ) -> WorkflowState:
        """
        Start the analysis phase (Agent 1).

        Args:
            resume: Original resume content
            job_description: Job description text (optional if job_url provided)
            job_url: Job posting URL (optional if job_description provided)

        Returns:
            Workflow state after analysis
        """
        # Create initial state
        initial_state = create_initial_state(
            resume=resume,
            job_description=job_description,
            job_url=job_url
        )

        # Run analysis workflow
        result = self.analysis_workflow.invoke(initial_state)

        return result

    def apply_modifications(self, state: WorkflowState) -> WorkflowState:
        """
        Apply modifications based on selected suggestions (Agent 2 + Agent 3).

        Args:
            state: Workflow state with selected suggestions

        Returns:
            Updated workflow state with modified resume and rescoring
        """
        # Run modification and rescoring workflow
        result = self.modification_workflow.invoke(state)

        return result

    def export_resume(self, state: WorkflowState) -> WorkflowState:
        """
        Export approved resume to PDF.

        Args:
            state: Workflow state with approved resume

        Returns:
            Updated workflow state with PDF output
        """
        # Run export workflow
        result = self.export_workflow.invoke(state)

        return result

    def update_suggestions(
        self,
        state: WorkflowState,
        selected_ids: list
    ) -> WorkflowState:
        """
        Update which suggestions are selected.

        Args:
            state: Current workflow state
            selected_ids: List of suggestion IDs to select

        Returns:
            Updated state with selection changes
        """
        if state.get("suggestions"):
            for suggestion in state["suggestions"]:
                suggestion["selected"] = suggestion["id"] in selected_ids

        return state

    def approve_resume(self, state: WorkflowState) -> WorkflowState:
        """
        Mark resume as approved.

        Args:
            state: Current workflow state

        Returns:
            Updated state with approval
        """
        state["approved"] = True
        return state

    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Get current workflow status and progress.

        Args:
            state: Current workflow state

        Returns:
            Status dictionary with stage, scores, and completion info
        """
        return {
            "stage": state.get("current_stage", "unknown"),
            "initial_score": state.get("initial_score"),
            "new_score": state.get("new_score"),
            "improvement": state.get("score_improvement"),
            "has_error": bool(state.get("error")),
            "error_message": state.get("error"),
            "approved": state.get("approved", False),
            "pdf_ready": bool(state.get("pdf_bytes")),
            "message_count": len(state.get("messages", []))
        }

    def run_full_workflow(
        self,
        resume: str,
        job_description: str,
        selected_suggestion_ids: list = None,
        auto_approve: bool = False
    ) -> WorkflowState:
        """
        Run the complete workflow in one go (for testing/automation).

        Args:
            resume: Original resume
            job_description: Job description
            selected_suggestion_ids: IDs of suggestions to apply (None = all)
            auto_approve: Whether to auto-approve and export

        Returns:
            Final workflow state
        """
        # Stage 1: Analysis
        state = self.start_analysis(resume, job_description)

        if state.get("error"):
            return state

        # Stage 2: Select suggestions
        if selected_suggestion_ids is not None:
            state = self.update_suggestions(state, selected_suggestion_ids)
        else:
            # Select all by default
            if state.get("suggestions"):
                ids = [s["id"] for s in state["suggestions"]]
                state = self.update_suggestions(state, ids)

        # Stage 3: Modify and rescore
        state = self.apply_modifications(state)

        if state.get("error"):
            return state

        # Stage 4: Export if approved
        if auto_approve:
            state = self.approve_resume(state)
            state = self.export_resume(state)

        return state
