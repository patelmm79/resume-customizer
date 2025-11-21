"""
Resume Customizer - Main Module

This module provides the core functionality for the resume customization system.
It can be used as a library or run directly for testing.

For the web interface, use: streamlit run app.py
"""

from agents.agent_1_scorer import ResumeScorerAgent
from agents.agent_2_modifier import ResumeModifierAgent
from agents.agent_3_rescorer import ResumeRescorerAgent
from utils.job_scraper import JobScraper
from utils.pdf_exporter import PDFExporter


class ResumeCustomizer:
    """Main class orchestrating the resume customization workflow."""

    def __init__(self):
        """Initialize all agents."""
        self.scorer = ResumeScorerAgent()
        self.modifier = ResumeModifierAgent()
        self.rescorer = ResumeRescorerAgent()
        self.scraper = JobScraper()
        self.exporter = PDFExporter()

    def analyze_resume(self, resume_content: str, job_description: str) -> dict:
        """
        Analyze resume and provide score with suggestions.

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
        Modify resume based on suggestions.

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
        Rescore modified resume.

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
        Export resume to PDF.

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
    """Example usage of the ResumeCustomizer."""
    print("Resume Customizer - Core Module")
    print("=" * 50)
    print("\nFor the web interface, run:")
    print("  streamlit run app.py")
    print("\nThis module provides the core functionality that")
    print("can be imported and used programmatically.")
    print("\nExample:")
    print("  from main import ResumeCustomizer")
    print("  customizer = ResumeCustomizer()")
    print("  result = customizer.analyze_resume(resume, job_desc)")
    print("=" * 50)


if __name__ == "__main__":
    main()
