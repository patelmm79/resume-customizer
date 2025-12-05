"""Agent 2: Resume Modifier."""
from typing import Dict, List
from utils.agent_helper import get_agent_llm_client
from utils.resume_standards import get_modification_prompt_prefix


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

        # Get centralized standards
        standards_prefix = get_modification_prompt_prefix()

        system_prompt = f"""{standards_prefix}

CRITICAL RULES FOR SKILLS:
- ONLY add skills that are EXPLICITLY listed in the suggestions provided
- DO NOT add any skills that are not in the approved suggestions list
- DO NOT infer or assume additional skills should be added
- If a skill is not in the suggestions, it must NOT appear in the modified resume unless it was already in the original resume

Return ONLY the modified resume in markdown format. Do not include any explanations or comments."""

        # Use edited_text if available, otherwise use original text
        suggestions_text = "\n".join([
            f"- [{s['category']}] {s.get('edited_text', s['text'])}"
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
- Some suggestions may have been edited by the user - use the EXACT text provided in each suggestion
- For Summary and Experience suggestions, the text provided may be the user's custom edit - apply it exactly as written
- For skills: Add ONLY the skills explicitly listed in the "Add skill:" suggestions above
- DO NOT add any skills from the job description that are not in the approved suggestions
- DO NOT add any skills that were not explicitly approved by the user
- If no skill suggestions were approved, do not modify the skills section beyond what's already there
- **ABSOLUTE REQUIREMENT**: Every job entry MUST retain its job headline (the italicized line after the job metadata). NEVER remove job headlines, even when removing bullet points.

❌ ABSOLUTELY FORBIDDEN - DO NOT TOUCH FORMATTING:
- NEVER change bold formatting (** or <b> tags)
- NEVER change italic formatting (* or <i> tags)
- NEVER change colors (HTML color tags or CSS)
- NEVER change font sizes, styles, or any visual formatting
- NEVER remove user's custom HTML/CSS formatting
- PRESERVE ALL existing formatting EXACTLY as it appears in the original
- Your ONLY job is to modify CONTENT based on approved suggestions
- Formatting changes are STRICTLY FORBIDDEN and handled by a different agent

Return the complete modified resume in markdown format with ALL ORIGINAL FORMATTING PRESERVED EXACTLY. Only change the content based on approved suggestions."""

        try:
            modified_resume = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5  # Lower temperature for more consistent output
            )

            # Clean up the response
            modified_resume = self._clean_resume(modified_resume)

            # NO AUTO-FIXES - Return resume as-is from LLM
            # Agent 4 will validate and report issues only
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
