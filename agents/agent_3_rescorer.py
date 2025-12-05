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
                - new_score: int (1-100)
                - comparison: str
                - improvements: List[str]
                - recommendation: str
        """
        system_prompt = """You are an expert resume evaluator. Your job is to:
1. Score a modified resume against a job description (1-100 scale)
2. Compare it to the original score
3. Identify specific improvements made
4. Provide a recommendation on whether the resume is ready

Be objective and thorough in your evaluation."""

        user_prompt = f"""Please evaluate this modified resume against the job description:

MODIFIED RESUME:
{modified_resume}

JOB DESCRIPTION:
{job_description}

ORIGINAL SCORE: {original_score}/100

Please provide:
1. A new compatibility score (1-100)
2. Key improvements you notice compared to the original
3. Any remaining concerns or areas for improvement
4. A recommendation (Ready to Submit / Needs More Work)
5. **CRITICAL**: If the new score is LOWER than the original score, you MUST explain why in the "score_drop_explanation" field

Please provide your response in VALID JSON format ONLY (no markdown, no code blocks, just pure JSON):

{{
  "new_score": 85,
  "comparison": "Brief comparison of how the resume has changed",
  "improvements": [
    "Added specific technical skills mentioned in job description",
    "Quantified achievements with metrics",
    "Improved professional summary alignment"
  ],
  "concerns": [
    "Could add more leadership examples",
    "Missing certification XYZ"
  ],
  "recommendation": "Ready to Submit",
  "reasoning": "Explanation of why ready or needs work",
  "score_drop_explanation": "ONLY IF NEW SCORE < ORIGINAL: Detailed explanation of why score dropped despite changes. What specific issues caused the lower score? What did the changes negatively impact?"
}}

CRITICAL:
- Return ONLY valid JSON, no markdown formatting, no ```json code blocks
- new_score must be 1-100
- recommendation must be either "Ready to Submit" or "Needs More Work"
- **If new_score < {original_score}, you MUST provide detailed score_drop_explanation**
- Be consistent in your scoring - don't drop scores without clear justification"""

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
            response: Raw LLM response (expected as JSON)
            original_score: Original score for comparison

        Returns:
            Structured dictionary with rescoring results
        """
        import json
        import re

        # Clean up response - remove markdown code blocks if present
        cleaned = response.strip()

        if cleaned.startswith("```"):
            first_newline = cleaned.find('\n')
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

        try:
            # Parse JSON
            parsed = json.loads(cleaned)

            new_score = parsed.get("new_score", original_score + 5)
            score_improvement = new_score - original_score

            result = {
                "new_score": new_score,
                "original_score": original_score,
                "score_improvement": score_improvement,
                "comparison": parsed.get("comparison", "Resume has been updated."),
                "improvements": parsed.get("improvements", []),
                "concerns": parsed.get("concerns", []),
                "recommendation": parsed.get("recommendation", "Needs More Work"),
                "reasoning": parsed.get("reasoning", "See improvements above.")
            }

            # CRITICAL: If score dropped, include explanation
            if new_score < original_score:
                score_drop = parsed.get("score_drop_explanation", "")
                if score_drop:
                    result["score_drop_explanation"] = score_drop
                else:
                    # Force LLM to explain if it didn't provide one
                    result["score_drop_explanation"] = "Score decreased without explanation - this may indicate scoring inconsistency."

            return result

        except json.JSONDecodeError as e:
            print(f"[Agent3 DEBUG] JSON parse failed: {str(e)}")

            # Fallback: Extract JSON from text
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    new_score = parsed.get("new_score", original_score + 5)
                    score_improvement = new_score - original_score

                    result = {
                        "new_score": new_score,
                        "original_score": original_score,
                        "score_improvement": score_improvement,
                        "comparison": parsed.get("comparison", "Resume has been updated."),
                        "improvements": parsed.get("improvements", []),
                        "concerns": parsed.get("concerns", []),
                        "recommendation": parsed.get("recommendation", "Needs More Work"),
                        "reasoning": parsed.get("reasoning", "See improvements above.")
                    }

                    if new_score < original_score:
                        result["score_drop_explanation"] = parsed.get("score_drop_explanation", "Score decreased without explanation.")

                    return result
                except json.JSONDecodeError:
                    pass

            # If all parsing fails, return safe defaults
            return {
                "new_score": original_score + 5,
                "original_score": original_score,
                "score_improvement": 5,
                "comparison": "Unable to parse scoring response.",
                "improvements": [],
                "concerns": ["Scoring error - please try again"],
                "recommendation": "Needs More Work",
                "reasoning": "Parsing failed."
            }
