"""Agent 6: Freeform Resume Editor."""
from typing import Dict
from utils.gemini_client import GeminiClient


class FreeformEditorAgent:
    """Agent that applies user-requested freeform changes to resume."""

    def __init__(self):
        """Initialize the freeform editor agent."""
        self.client = GeminiClient()

    def apply_changes(
        self,
        resume_content: str,
        user_request: str,
        job_description: str
    ) -> Dict:
        """
        Apply user-requested changes to the resume.

        Args:
            resume_content: Current resume in markdown format
            user_request: User's freeform change request
            job_description: Job description for context

        Returns:
            Dictionary containing:
                - modified_resume: str (resume with changes applied)
                - changes_summary: str (summary of what was changed)
        """
        system_prompt = """You are an expert resume editor. Your job is to:
1. Carefully read the user's requested changes
2. Apply those changes to the resume precisely
3. Maintain professional formatting and structure
4. Ensure changes align with the job description
5. Keep the resume concise and impactful

IMPORTANT:
- Apply EXACTLY what the user requests
- Do not add unrequested changes
- Maintain markdown formatting
- Keep the resume professional and ATS-friendly
- Preserve information the user didn't ask to change"""

        user_prompt = f"""Please apply the following changes to this resume:

USER'S REQUESTED CHANGES:
{user_request}

CURRENT RESUME:
{resume_content}

JOB DESCRIPTION (for context):
{job_description}

Please format your response EXACTLY as follows:

MODIFIED_RESUME:
[Your modified resume in markdown format here]

CHANGES_SUMMARY:
[Brief summary of what changes you made]

Apply the user's requested changes while maintaining professional quality and alignment with the job description."""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5  # Balanced between creativity and consistency
            )

            return self._parse_response(response)

        except Exception as e:
            raise Exception(f"Freeform editing failed: {str(e)}")

    def _parse_response(self, response: str) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response

        Returns:
            Structured dictionary with modified resume and summary
        """
        lines = response.strip().split('\n')

        modified_resume = []
        changes_summary = ""
        current_section = None

        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith("MODIFIED_RESUME:"):
                current_section = "modified_resume"
                continue

            elif stripped_line.startswith("CHANGES_SUMMARY:"):
                current_section = "changes_summary"
                continue

            # Collect content for each section
            if current_section == "modified_resume":
                if not stripped_line.startswith("CHANGES_SUMMARY:"):
                    modified_resume.append(line)

            elif current_section == "changes_summary":
                if stripped_line:
                    changes_summary += stripped_line + " "

        # Join modified resume
        modified_resume_text = '\n'.join(modified_resume).strip()

        # Clean up markdown code blocks if present
        if modified_resume_text.startswith("```"):
            lines = modified_resume_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            modified_resume_text = '\n'.join(lines).strip()

        return {
            "modified_resume": modified_resume_text,
            "changes_summary": changes_summary.strip() if changes_summary else "Changes applied as requested."
        }
