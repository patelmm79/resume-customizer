"""Agent 3: Resume Re-scorer and Approval."""
from typing import Dict
from utils.gemini_client import GeminiClient


class ResumeRescorerAgent:
    """Agent that rescores modified resumes and requests approval."""

    def __init__(self):
        """Initialize the rescorer agent."""
        self.client = GeminiClient()

    def rescore_resume(
        self,
        modified_resume: str,
        job_description: str,
        original_score: int
    ) -> Dict:
        """
        Rescore the modified resume and provide comparison.

        Args:
            modified_resume: Modified resume in markdown
            job_description: The job description
            original_score: The original compatibility score

        Returns:
            Dictionary containing:
                - new_score: int (1-10)
                - comparison: str
                - improvements: List[str]
                - recommendation: str
        """
        system_prompt = """You are an expert resume evaluator. Your job is to:
1. Score a modified resume against a job description (1-10 scale)
2. Compare it to the original score
3. Identify specific improvements made
4. Provide a recommendation on whether the resume is ready

Be objective and thorough in your evaluation."""

        user_prompt = f"""Please evaluate this modified resume against the job description:

MODIFIED RESUME:
{modified_resume}

JOB DESCRIPTION:
{job_description}

ORIGINAL SCORE: {original_score}/10

Please provide:
1. A new compatibility score (1-10)
2. Key improvements you notice compared to the original
3. Any remaining concerns or areas for improvement
4. A recommendation (Ready to Submit / Needs More Work)

Format your response EXACTLY as follows:

NEW_SCORE: [number from 1-10]

COMPARISON:
[Brief comparison of improvement]

IMPROVEMENTS:
- Improvement 1
- Improvement 2
- Improvement 3
(Continue as needed)

REMAINING_CONCERNS:
- Concern 1 (if any)
- Concern 2 (if any)

RECOMMENDATION: [Ready to Submit / Needs More Work]

REASONING:
[Explain your recommendation]"""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.6
            )

            return self._parse_response(response, original_score)

        except Exception as e:
            raise Exception(f"Error rescoring resume: {str(e)}")

    def _parse_response(self, response: str, original_score: int) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response
            original_score: Original score for comparison

        Returns:
            Structured dictionary with rescoring results
        """
        lines = response.strip().split('\n')

        new_score = None
        comparison = []
        improvements = []
        concerns = []
        recommendation = "Needs More Work"
        reasoning = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("NEW_SCORE:"):
                score_text = line.replace("NEW_SCORE:", "").strip()
                try:
                    new_score = int(score_text)
                except ValueError:
                    import re
                    match = re.search(r'\d+', score_text)
                    if match:
                        new_score = int(match.group())
                    else:
                        new_score = original_score + 1
                current_section = "score"

            elif line.startswith("COMPARISON:"):
                current_section = "comparison"

            elif line.startswith("IMPROVEMENTS:"):
                current_section = "improvements"

            elif line.startswith("REMAINING_CONCERNS:"):
                current_section = "concerns"

            elif line.startswith("RECOMMENDATION:"):
                rec_text = line.replace("RECOMMENDATION:", "").strip()
                if "Ready" in rec_text or "ready" in rec_text:
                    recommendation = "Ready to Submit"
                else:
                    recommendation = "Needs More Work"
                current_section = "recommendation"

            elif line.startswith("REASONING:"):
                current_section = "reasoning"

            elif line and current_section == "comparison":
                if not line.startswith(("IMPROVEMENTS:", "NEW_SCORE:", "REMAINING_CONCERNS:", "RECOMMENDATION:", "REASONING:")):
                    comparison.append(line)

            elif line and current_section == "improvements" and line.startswith("-"):
                improvements.append(line[1:].strip())

            elif line and current_section == "concerns" and line.startswith("-"):
                concerns.append(line[1:].strip())

            elif line and current_section == "reasoning":
                if not line.startswith(("IMPROVEMENTS:", "NEW_SCORE:", "REMAINING_CONCERNS:", "RECOMMENDATION:", "COMPARISON:")):
                    reasoning.append(line)

        # Ensure new_score is valid
        if new_score is None or new_score < 1 or new_score > 10:
            new_score = min(10, original_score + 1)

        # Calculate improvement
        score_improvement = new_score - original_score

        return {
            "new_score": new_score,
            "original_score": original_score,
            "score_improvement": score_improvement,
            "comparison": "\n".join(comparison) if comparison else "Resume has been updated based on suggestions.",
            "improvements": improvements,
            "concerns": concerns,
            "recommendation": recommendation,
            "reasoning": "\n".join(reasoning) if reasoning else "See improvements above."
        }
