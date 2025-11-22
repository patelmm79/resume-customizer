"""Agent 2: Resume Modifier."""
from typing import Dict, List
from utils.agent_helper import get_agent_llm_client


class ResumeModifierAgent:
    """Agent that modifies resumes based on suggestions."""

    def __init__(self):
        """Initialize the modifier agent."""
        self.client = get_agent_llm_client()

    def modify_resume(
        self,
        original_resume: str,
        suggestions: List[Dict],
        job_description: str
    ) -> str:
        """
        Modify resume based on selected suggestions.

        Args:
            original_resume: Original resume in markdown
            suggestions: List of suggestion dictionaries with 'id', 'text', 'category', 'selected'
            job_description: The target job description

        Returns:
            Modified resume in markdown format
        """
        # Filter only selected suggestions
        selected_suggestions = [
            s for s in suggestions if s.get("selected", False)
        ]

        if not selected_suggestions:
            return original_resume

        system_prompt = """You are an expert resume writer and editor. Your job is to:
1. Modify a resume based on specific suggestions
2. Maintain professional markdown formatting
3. Keep the resume to approximately 1 page (aim for 500-700 words)
4. Optimize for ATS (Applicant Tracking Systems)
5. Use strong action verbs and quantifiable achievements
6. Ensure the resume is tailored to the target job

IMPORTANT CONSTRAINTS:
- Keep it concise - prioritize relevance over length
- Remove or minimize irrelevant information
- Use bullet points for readability
- Maintain proper markdown structure
- Focus on impact and results

CRITICAL RULE FOR SKILLS:
- ONLY add skills that are EXPLICITLY listed in the suggestions provided
- DO NOT add any skills that are not in the approved suggestions list
- DO NOT infer or assume additional skills should be added
- If a skill is not in the suggestions, it must NOT appear in the modified resume unless it was already in the original resume

GUIDANCE FOR SUMMARY SECTION:
Craft a summary that bests aligns with the stated job description, emphasizing relevant qualifications and incorporating key responsibilities and skills from the job description.  Ensure each bullet point best describes the action taken and the result achieved.

GUIDANCE FOR MODIFYING BULLET POINTS FOR JOBS:
Polish the description of the three most recent positions to showcase how the experience best aligns with the requirements of the role.

Return ONLY the modified resume in markdown format. Do not include any explanations or comments."""

        suggestions_text = "\n".join([
            f"- [{s['category']}] {s['text']}"
            for s in selected_suggestions
        ])

        user_prompt = f"""Please modify the following resume based on these suggestions, keeping it to approximately 1 page:

ORIGINAL RESUME:
{original_resume}

SUGGESTIONS TO IMPLEMENT (USER APPROVED):
{suggestions_text}

TARGET JOB DESCRIPTION (for context only):
{job_description}

CRITICAL INSTRUCTIONS:
- Apply ONLY the suggestions listed above that the user approved
- For skills: Add ONLY the skills explicitly listed in the "Add skill:" suggestions above
- DO NOT add any skills from the job description that are not in the approved suggestions
- DO NOT add any skills that were not explicitly approved by the user
- If no skill suggestions were approved, do not modify the skills section beyond what's already there

Return the complete modified resume in markdown format. Maintain the structure but apply all suggestions while keeping it concise and focused on relevance to the job."""

        try:
            modified_resume = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5  # Lower temperature for more consistent output
            )

            # Clean up the response
            modified_resume = self._clean_resume(modified_resume)

            return modified_resume

        except Exception as e:
            raise Exception(f"Error modifying resume: {str(e)}")

    def _clean_resume(self, resume: str) -> str:
        """
        Clean up the resume output.

        Args:
            resume: Raw resume text

        Returns:
            Cleaned resume
        """
        # Remove any markdown code blocks if present
        if resume.startswith("```"):
            lines = resume.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            resume = '\n'.join(lines)

        return resume.strip()
