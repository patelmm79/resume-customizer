"""
Resume Customizer - Main Module with LangGraph Orchestration

This module provides the core functionality for the resume customization system
using LangGraph for agent orchestration.

For the web interface, use: streamlit run app.py
"""

from workflow.orchestrator import ResumeWorkflowOrchestrator
from workflow.state import WorkflowState
from utils.langsmith_config import configure_langsmith

# Configure LangSmith tracing at module load
configure_langsmith()


class ResumeCustomizer:
    """
    Main class orchestrating the resume customization workflow using LangGraph.

    This class provides a clean interface for executing the multi-stage workflow
    with human-in-the-loop interactions.
    """

    def __init__(self):
        """Initialize the LangGraph orchestrator."""
        self.orchestrator = ResumeWorkflowOrchestrator()

    def start_workflow(
        self,
        resume: str,
        job_description: str = None,
        job_url: str = None
    ) -> WorkflowState:
        """
        Start the resume customization workflow.

        Args:
            resume: Original resume content
            job_description: Job description text (optional if job_url provided)
            job_url: Job posting URL (optional if job_description provided)

        Returns:
            Workflow state after analysis
        """
        return self.orchestrator.start_analysis(resume, job_description, job_url)

    def continue_workflow(self, state: WorkflowState) -> WorkflowState:
        """
        Continue workflow after suggestion selection.

        Args:
            state: Workflow state with selected suggestions

        Returns:
            Updated workflow state with modifications
        """
        return self.orchestrator.apply_modifications(state)

    def finalize_workflow(self, state: WorkflowState) -> WorkflowState:
        """
        Finalize workflow and export PDF.

        Args:
            state: Workflow state with approved resume

        Returns:
            Final workflow state with PDF
        """
        state = self.orchestrator.approve_resume(state)
        return self.orchestrator.export_resume(state)

    def run_complete_workflow(
        self,
        resume: str,
        job_description: str,
        auto_select_all: bool = True,
        auto_approve: bool = False
    ) -> WorkflowState:
        """
        Run the complete workflow end-to-end (useful for testing).

        Args:
            resume: Original resume
            job_description: Job description
            auto_select_all: Automatically select all suggestions
            auto_approve: Automatically approve and export

        Returns:
            Final workflow state
        """
        return self.orchestrator.run_full_workflow(
            resume=resume,
            job_description=job_description,
            selected_suggestion_ids=None if auto_select_all else [],
            auto_approve=auto_approve
        )

    def get_status(self, state: WorkflowState) -> dict:
        """
        Get workflow status.

        Args:
            state: Current workflow state

        Returns:
            Status dictionary
        """
        return self.orchestrator.get_workflow_status(state)


def main():
    """Example usage of the ResumeCustomizer with LangGraph."""
    print("Resume Customizer - LangGraph Orchestration")
    print("=" * 60)
    print("\nFor the web interface, run:")
    print("  streamlit run app.py")
    print("\nProgrammatic Usage:")
    print("  from main import ResumeCustomizer")
    print("  customizer = ResumeCustomizer()")
    print("")
    print("  # Start workflow")
    print("  state = customizer.start_workflow(resume, job_desc)")
    print("")
    print("  # Continue after suggestion selection")
    print("  state = customizer.continue_workflow(state)")
    print("")
    print("  # Finalize and export")
    print("  final_state = customizer.finalize_workflow(state)")
    print("")
    print("Or run everything at once:")
    print("  state = customizer.run_complete_workflow(resume, job_desc)")
    print("=" * 60)


if __name__ == "__main__":
    main()
