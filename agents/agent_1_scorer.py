"""Agent 1: Resume Scorer and Analyzer."""
from typing import Dict, List
from utils.agent_helper import get_agent_llm_client


class ResumeScorerAgent:
    """Agent that scores resumes and suggests improvements."""

    def __init__(self):
        """Initialize the scorer agent."""
        self.client = get_agent_llm_client()

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
                - score: int (1-100)
                - analysis: str
                - suggestions: List[Dict] with 'id', 'text', and 'category'
        """
        system_prompt = """You are an expert resume analyzer and career coach. Your job is to:
1. Carefully compare a resume against a job description
2. Provide a compatibility score from 1-100 (where 100 is perfect match)
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
- ONLY suggest skills that are NOT already present in the resume (check the Skills section carefully)
- Do NOT suggest skills that already appear in the resume, even with slightly different wording
- Each skill should be its own suggestion so the user can selectively approve which skills to add
- Only skills that are checked will be added to the resume

IMPORTANT for Summary and Experience suggestions:
- For Summary: Provide the ACTUAL suggested summary text, not just a description of what to change
- For Experience: Provide the ACTUAL suggested bullet point or text, not just instructions
- Users will be able to edit this text before applying it
- Make suggestions specific and ready-to-use

Be specific and actionable in your suggestions."""

        user_prompt = f"""Please analyze this resume against the job description and provide:

1. A score from 1-100 for how well this resume matches the job
2. A brief analysis explaining the score
3. A list of specific, actionable suggestions for improvement

RESUME:
{resume_content}

JOB DESCRIPTION:
{job_description}

Please format your response EXACTLY as follows:

SCORE: [number from 1-100]

ANALYSIS:
[Your detailed analysis here]

SUGGESTIONS:
- [CATEGORY: Skills] Add skill: Python
- [CATEGORY: Skills] Add skill: Docker
- [CATEGORY: Skills] Add skill: Kubernetes
- [CATEGORY: Summary] [DESCRIPTION: Emphasize cloud architecture and leadership experience] [SUGGESTED_TEXT: Results-driven Data Scientist with 8+ years of experience building ML pipelines and deploying models at scale. Proven track record of reducing infrastructure costs by 40% through optimization and driving data-driven decision making across cross-functional teams.]
- [CATEGORY: Experience] [DESCRIPTION: Quantify achievement in recent engineering role] [SUGGESTED_TEXT: Led a team of 5 engineers to architect and deploy a real-time fraud detection system processing 10M+ transactions daily, reducing false positives by 35% and saving $2M annually.]
(Continue with more suggestions as needed)

CRITICAL FORMAT REQUIREMENTS:

For Skills:
- BEFORE suggesting a skill, carefully check if it already exists in the resume's Skills section
- Do NOT suggest skills that are already listed (e.g., if "Tableau" is in the resume, don't suggest adding it)
- Do NOT suggest skills with slightly different wording (e.g., if "Stakeholder Management" is listed, don't suggest "Stakeholder Engagement")
- Only suggest skills that are genuinely missing but relevant to the job description
- For skills, create ONE suggestion per skill
- Each skill should be its own line item so the user can individually approve which skills to add
- Format: "Add skill: [Skill Name]"

For Summary and Experience:
- Use this format: [DESCRIPTION: Brief justification] [SUGGESTED_TEXT: Actual text to use]
- DESCRIPTION: A brief phrase explaining why this change is suggested (shown in checkbox)
- SUGGESTED_TEXT: The COMPLETE actual text to insert/replace (shown in text box)
- For Summary: Provide a complete paragraph rewrite
- For Experience: Provide a complete bullet point with metrics and impact
- Do NOT write vague instructions - always provide concrete, ready-to-use text
- Users will be able to edit the SUGGESTED_TEXT before applying it

Skills not checked will NOT be added to the resume"""

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

                # Extract DESCRIPTION and SUGGESTED_TEXT if present
                description = None
                suggested_text = None

                if "[DESCRIPTION:" in suggestion_text:
                    # Extract description
                    desc_start = suggestion_text.find("[DESCRIPTION:") + 13
                    desc_end = suggestion_text.find("]", desc_start)
                    if desc_end != -1:
                        description = suggestion_text[desc_start:desc_end].strip()
                        suggestion_text = suggestion_text[desc_end + 1:].strip()

                if "[SUGGESTED_TEXT:" in suggestion_text:
                    # Extract suggested text
                    text_start = suggestion_text.find("[SUGGESTED_TEXT:") + 16
                    text_end = suggestion_text.find("]", text_start)
                    if text_end != -1:
                        suggested_text = suggestion_text[text_start:text_end].strip()
                        suggestion_text = suggestion_text[text_end + 1:].strip()

                # If we have both description and suggested_text, use description for display
                if description and suggested_text:
                    display_text = description
                    edited_text = suggested_text
                else:
                    # For simple suggestions (like Skills), just use the text as-is
                    display_text = suggestion_text
                    edited_text = suggestion_text

                suggestions.append({
                    "id": len(suggestions),
                    "text": display_text,
                    "category": category,
                    "selected": True,  # Default to selected
                    "edited_text": edited_text  # Pre-populate with suggested text
                })

        # Ensure score is valid
        if score is None or score < 1 or score > 100:
            score = 50

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
                - score: int (1-100)
                - analysis: str (brief evaluation)
        """
        system_prompt = """You are an expert resume analyzer. Your job is to:
1. Carefully compare a resume against a job description
2. Provide a compatibility score from 1-100 (where 100 is perfect match)
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

SCORE: [number from 1-100]

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
                            score = 50
                    current_section = "score"

                elif line.startswith("ANALYSIS:"):
                    current_section = "analysis"

                elif line and current_section == "analysis":
                    analysis.append(line)

            if score is None or score < 1 or score > 100:
                score = 50

            return {
                "score": score,
                "analysis": "\n".join(analysis)
            }

        except Exception as e:
            raise Exception(f"Error in resume scoring: {str(e)}")
