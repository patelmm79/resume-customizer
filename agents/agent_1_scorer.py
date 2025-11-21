"""Agent 1: Resume Scorer and Analyzer."""
from typing import Dict, List
from utils.gemini_client import GeminiClient


class ResumeScorerAgent:
    """Agent that scores resumes and suggests improvements."""

    def __init__(self):
        """Initialize the scorer agent."""
        self.client = GeminiClient()

    def analyze_and_score(
        self,
        resume_content: str,
        job_description: str
    ) -> Dict:
        """
        Analyze resume against job description and provide score with suggestions.

        Args:
            resume_content: The resume in markdown format
            job_description: The job description text

        Returns:
            Dictionary containing:
                - score: int (1-10)
                - analysis: str
                - suggestions: List[Dict] with 'id', 'text', and 'category'
        """
        system_prompt = """You are an expert resume analyzer and career coach. Your job is to:
1. Carefully compare a resume against a job description
2. Provide a compatibility score from 1-10 (where 10 is perfect match)
3. Identify specific, actionable improvements

Focus on:
- Keyword matching and ATS optimization
- Relevant skills and experience alignment
- Quantifiable achievements
- Professional summary optimization
- Removing irrelevant information
- Highlighting transferable skills

IMPORTANT for Skills:
- Create a SEPARATE checklist item for EACH individual skill from the job description
- Include skills that are important in the job description, even if not mentioned in the resume
- Each skill should be its own suggestion so the user can selectively approve which skills to add
- Only skills that are checked will be added to the resume

Be specific and actionable in your suggestions."""

        user_prompt = f"""Please analyze this resume against the job description and provide:

1. A score from 1-10 for how well this resume matches the job
2. A brief analysis explaining the score
3. A list of specific, actionable suggestions for improvement

RESUME:
{resume_content}

JOB DESCRIPTION:
{job_description}

Please format your response EXACTLY as follows:

SCORE: [number from 1-10]

ANALYSIS:
[Your detailed analysis here]

SUGGESTIONS:
- [CATEGORY: Skills] Add skill: Python
- [CATEGORY: Skills] Add skill: Docker
- [CATEGORY: Skills] Add skill: Kubernetes
- [CATEGORY: Experience] Quantify achievement in role X with specific metrics
- [CATEGORY: Summary] Rewrite summary to emphasize Y
(Continue with more suggestions as needed)

IMPORTANT: For skills, create ONE suggestion per skill. Each skill should be its own line item so the user can individually approve which skills to add. Only include skills that are relevant to the job description. Skills not checked will NOT be added to the resume."""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )

            return self._parse_response(response)

        except Exception as e:
            raise Exception(f"Error in resume analysis: {str(e)}")

    def _parse_response(self, response: str) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response

        Returns:
            Structured dictionary with score, analysis, and suggestions
        """
        lines = response.strip().split('\n')

        score = None
        analysis = []
        suggestions = []
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("SCORE:"):
                score_text = line.replace("SCORE:", "").strip()
                try:
                    score = int(score_text)
                except ValueError:
                    # Try to extract first number
                    import re
                    match = re.search(r'\d+', score_text)
                    if match:
                        score = int(match.group())
                    else:
                        score = 5  # Default
                current_section = "score"

            elif line.startswith("ANALYSIS:"):
                current_section = "analysis"

            elif line.startswith("SUGGESTIONS:"):
                current_section = "suggestions"

            elif line and current_section == "analysis" and not line.startswith("SUGGESTIONS:"):
                analysis.append(line)

            elif line and current_section == "suggestions" and line.startswith("-"):
                # Parse suggestion with category
                suggestion_text = line[1:].strip()  # Remove leading '-'

                # Extract category if present
                category = "General"
                if suggestion_text.startswith("[CATEGORY:"):
                    end_bracket = suggestion_text.find("]")
                    if end_bracket != -1:
                        category = suggestion_text[10:end_bracket].strip()
                        suggestion_text = suggestion_text[end_bracket + 1:].strip()

                suggestions.append({
                    "id": len(suggestions),
                    "text": suggestion_text,
                    "category": category,
                    "selected": True  # Default to selected
                })

        # Ensure score is valid
        if score is None or score < 1 or score > 10:
            score = 5

        return {
            "score": score,
            "analysis": "\n".join(analysis),
            "suggestions": suggestions
        }

    def score_only(
        self,
        resume_content: str,
        job_description: str
    ) -> Dict:
        """
        Score resume against job description without generating suggestions.
        Used for rescoring and final scoring.

        Args:
            resume_content: The resume in markdown format
            job_description: The job description text

        Returns:
            Dictionary containing:
                - score: int (1-10)
                - analysis: str (brief evaluation)
        """
        system_prompt = """You are an expert resume analyzer. Your job is to:
1. Carefully compare a resume against a job description
2. Provide a compatibility score from 1-10 (where 10 is perfect match)
3. Provide brief analysis of the match quality

Focus on:
- Keyword matching and ATS optimization
- Relevant skills and experience alignment
- Overall suitability for the role"""

        user_prompt = f"""Please score this resume against the job description:

RESUME:
{resume_content}

JOB DESCRIPTION:
{job_description}

Please format your response EXACTLY as follows:

SCORE: [number from 1-10]

ANALYSIS:
[Your brief analysis of the match quality and key strengths]"""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )

            # Parse just score and analysis
            lines = response.strip().split('\n')
            score = None
            analysis = []
            current_section = None

            for line in lines:
                line = line.strip()

                if line.startswith("SCORE:"):
                    score_text = line.replace("SCORE:", "").strip()
                    try:
                        score = int(score_text)
                    except ValueError:
                        import re
                        match = re.search(r'\d+', score_text)
                        if match:
                            score = int(match.group())
                        else:
                            score = 5
                    current_section = "score"

                elif line.startswith("ANALYSIS:"):
                    current_section = "analysis"

                elif line and current_section == "analysis":
                    analysis.append(line)

            if score is None or score < 1 or score > 10:
                score = 5

            return {
                "score": score,
                "analysis": "\n".join(analysis)
            }

        except Exception as e:
            raise Exception(f"Error in resume scoring: {str(e)}")
