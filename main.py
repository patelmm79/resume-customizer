"""
Resume Customizer - Main Module with LangGraph Orchestration

This module provides the core functionality for the resume customization system
using LangGraph for agent orchestration.

For the web interface, use: streamlit run app.py
"""

from workflow.orchestrator import ResumeWorkflowOrchestrator
from workflow.state import WorkflowState

# Legacy compatibility wrapper
from agents.agent_1_scorer import ResumeScorerAgent
from agents.agent_2_modifier import ResumeModifierAgent
from agents.agent_3_rescorer import ResumeRescorerAgent
from utils.job_scraper import JobScraper
from utils.pdf_exporter import PDFExporter


class ResumeCustomizer:
    """
    Main class orchestrating the resume customization workflow.

    Now uses LangGraph for agent orchestration instead of manual sequencing.
    Provides both the new LangGraph interface and legacy compatibility methods.
    """

    def __init__(self):
        """Initialize the LangGraph orchestrator."""
        self.orchestrator = ResumeWorkflowOrchestrator()

        # Keep legacy agents for backward compatibility
        self.scorer = ResumeScorerAgent()
        self.modifier = ResumeModifierAgent()
        self.rescorer = ResumeRescorerAgent()
        self.scraper = JobScraper()
        self.exporter = PDFExporter()

    # New LangGraph-based methods

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

    # Legacy compatibility methods (kept for backward compatibility)

    def analyze_resume(self, resume_content: str, job_description: str) -> dict:
        """
        [LEGACY] Analyze resume and provide score with suggestions.

        Note: Consider using start_workflow() for LangGraph orchestration.

        Args:
            resume_content: Resume in markdown format
            job_description: Job description text

        Returns:
            Dictionary with score, analysis, and suggestions
        """
        return self.scorer.analyze_and_score(resume_content, job_description)

    def modify_resume(
        self,
        resume_content: str,
        suggestions: list,
        job_description: str
    ) -> str:
        """
        [LEGACY] Modify resume based on suggestions.

        Note: Consider using continue_workflow() for LangGraph orchestration.

        Args:
            resume_content: Original resume
            suggestions: List of suggestions
            job_description: Target job description

        Returns:
            Modified resume in markdown
        """
        return self.modifier.modify_resume(
            resume_content,
            suggestions,
            job_description
        )

    def rescore_resume(
        self,
        modified_resume: str,
        job_description: str,
        original_score: int
    ) -> dict:
        """
        [LEGACY] Rescore modified resume.

        Note: This is now part of continue_workflow() in LangGraph orchestration.

        Args:
            modified_resume: Modified resume content
            job_description: Job description
            original_score: Original compatibility score

        Returns:
            Dictionary with new score and comparison
        """
        return self.rescorer.rescore_resume(
            modified_resume,
            job_description,
            original_score
        )

    def export_to_pdf(self, resume_content: str, filename: str = None) -> str:
        """
        [LEGACY] Export resume to PDF.

        Note: Consider using finalize_workflow() for LangGraph orchestration.

        Args:
            resume_content: Resume in markdown
            filename: Output filename

        Returns:
            Path to saved PDF
        """
        return self.exporter.markdown_to_pdf(resume_content, filename)

    def fetch_job_description(self, url: str) -> str:
        """
        Fetch job description from URL.

        Args:
            url: Job posting URL

        Returns:
            Job description text
        """
        return self.scraper.fetch_job_description(url)


def main():
    """Example usage of the ResumeCustomizer with LangGraph."""
    print("Resume Customizer - LangGraph Orchestration")
    print("=" * 60)
    print("\nFor the web interface, run:")
    print("  streamlit run app.py")
    print("\nThis module now uses LangGraph for agent orchestration!")
    print("\nNew LangGraph-based interface:")
    print("  from main import ResumeCustomizer")
    print("  customizer = ResumeCustomizer()")
    print("  ")
    print("  # Start workflow")
    print("  state = customizer.start_workflow(resume, job_desc)")
    print("  ")
    print("  # Continue after suggestion selection")
    print("  state = customizer.continue_workflow(state)")
    print("  ")
    print("  # Finalize and export")
    print("  state = customizer.finalize_workflow(state)")
    print("\nOr run everything at once:")
    print("  state = customizer.run_complete_workflow(resume, job_desc)")
    print("\nLegacy methods still available for backward compatibility.")
    print("=" * 60)


if __name__ == "__main__":
    main()
