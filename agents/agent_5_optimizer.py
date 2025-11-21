"""Agent 5: Resume Length Optimizer."""
from typing import Dict
from utils.gemini_client import GeminiClient


class ResumeOptimizerAgent:
    """Agent that optimizes resume length while maintaining score."""

    def __init__(self):
        """Initialize the optimizer agent."""
        self.client = GeminiClient()

    def optimize_resume(
        self,
        resume_content: str,
        job_description: str,
        current_score: int
    ) -> Dict:
        """
        Optimize resume to be as concise as possible without impacting score.

        Args:
            resume_content: Resume in markdown format
            job_description: Job description for context
            current_score: The current compatibility score to maintain

        Returns:
            Dictionary containing:
                - optimized_resume: str (optimized resume content)
                - word_count_before: int
                - word_count_after: int
                - optimization_summary: str
                - changes_made: List[str]
        """
        system_prompt = """You are an expert resume optimizer specializing in concise, impactful writing. Your job is to:
1. Make the resume as concise as possible while maintaining its effectiveness
2. Remove redundancy, wordiness, and unnecessary details
3. Keep all critical information that contributes to the job match
4. Aim for 1 page (approximately 500-700 words maximum)
5. Maintain or improve the compatibility score

Optimization strategies:
- Remove redundant phrases and filler words
- Combine similar bullet points
- Use stronger, more concise action verbs
- Remove less relevant experiences if space is tight
- Consolidate skills into efficient lists
- Ensure every word adds value

CRITICAL: Do not remove information that is directly relevant to the job description. The goal is conciseness without sacrificing match quality."""

        user_prompt = f"""Please optimize this resume to be as concise as possible while maintaining a compatibility score of {current_score}/10 with the job description.

CURRENT RESUME:
{resume_content}

JOB DESCRIPTION:
{job_description}

TARGET: Ideally 1 page (500-700 words). Current resume should be shortened without losing relevance.

Please format your response EXACTLY as follows:

OPTIMIZED_RESUME:
[Your optimized resume in markdown format here]

OPTIMIZATION_SUMMARY:
[Brief summary of what was optimized and why]

CHANGES_MADE:
- Change 1 description
- Change 2 description
- Change 3 description
(List all optimization changes made)

Ensure the optimized resume maintains all key information relevant to the job while being maximally concise."""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4  # Lower temperature for consistent optimization
            )

            return self._parse_response(response, resume_content)

        except Exception as e:
            raise Exception(f"Optimization failed: {str(e)}")

    def _parse_response(self, response: str, original_resume: str) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response
            original_resume: Original resume for comparison

        Returns:
            Structured dictionary with optimization results
        """
        lines = response.strip().split('\n')

        optimized_resume = []
        optimization_summary = ""
        changes_made = []
        current_section = None

        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith("OPTIMIZED_RESUME:"):
                current_section = "optimized_resume"
                continue

            elif stripped_line.startswith("OPTIMIZATION_SUMMARY:"):
                current_section = "optimization_summary"
                continue

            elif stripped_line.startswith("CHANGES_MADE:"):
                current_section = "changes_made"
                continue

            # Collect content for each section
            if current_section == "optimized_resume":
                if not stripped_line.startswith(("OPTIMIZATION_SUMMARY:", "CHANGES_MADE:")):
                    optimized_resume.append(line)

            elif current_section == "optimization_summary":
                if not stripped_line.startswith("CHANGES_MADE:") and stripped_line:
                    optimization_summary += stripped_line + " "

            elif current_section == "changes_made":
                if stripped_line.startswith("-"):
                    change_text = stripped_line[1:].strip()
                    changes_made.append(change_text)

        # Join optimized resume
        optimized_resume_text = '\n'.join(optimized_resume).strip()

        # Clean up markdown code blocks if present
        if optimized_resume_text.startswith("```"):
            lines = optimized_resume_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            optimized_resume_text = '\n'.join(lines).strip()

        # Calculate word counts
        word_count_before = len(original_resume.split())
        word_count_after = len(optimized_resume_text.split())

        return {
            "optimized_resume": optimized_resume_text,
            "word_count_before": word_count_before,
            "word_count_after": word_count_after,
            "words_removed": word_count_before - word_count_after,
            "optimization_summary": optimization_summary.strip() if optimization_summary else "Resume optimized for length.",
            "changes_made": changes_made if changes_made else ["Resume condensed while maintaining key information"]
        }
