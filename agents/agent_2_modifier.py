"""Agent 2: Resume Modifier."""
from typing import Dict, List
from utils.agent_helper import get_agent_llm_client
from utils.resume_validator import ResumeStructureValidator


class ResumeModifierAgent:
    """Agent that modifies resumes based on suggestions."""

    def __init__(self):
        """Initialize the modifier agent."""
        self.client = get_agent_llm_client()
        self.validator = ResumeStructureValidator()

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

Description of resume structure:

- The header of the resume contains the candidate name, contact information, and most likely a headline that describes the candidate in no more than 10 words.
- The sections of the resume include:
--Summary: This section is a paragraph that summarizes the candidate and his experience.
--Experience: This section shows the job history of the candidate.  See below for additional description of Experience section
--Skills: This section is a list of key technical and strategic skills.
--Key Achievements: This section is a set of 2-3 bullet points that outlines the candidate's key achievements.
--Education: This section lists the candidate's education history, focusing on degrees obtained.
--Certifications: This section lists the certifications obtained by the candidate. 

Description of Experience section:
- The following is an example of one job in Markdown format:
"**Advisor in Data Science and AI** | <span style="color: #1a73e8;">**Freelance**</span> | New York, NY, USA | *Mar 2025 - Present*\
*Provided strategic advice & built solutions to accelerate digital transformation, automation, and cost control using agentic AI.*
* Built an LLM service for less than $2 per day by containerizing open-source LLM, using Gemma from Hugging Face and deploying on Google Cloud Run.
* Created agentic AI application that triggers GitHub issues automatically by analyzing application logs, which flagged 4 problems and potential solutions.
* Devised an agentic AI web search summary tool to accelerate company research from 4 hours to 5 minutes,  Used LangGraph for agent orchestration, and Claude code as coding assistant."
--Row 1 contains the job title, company, location, and date range. CRITICAL: This row MUST end with a backslash "\" character. We will call this row "job metadata".
--Row 2 contains a high-level description of the company and the role, and is marked in *italics*. CRITICAL: This row must appear IMMEDIATELY after Row 1 with NO blank lines in between. The backslash "\" at the end of Row 1 creates the line break. We will call this row "job headline".
--Rows 3, 4, and 5 are bullet points listing achievements in the role. The number of bullet points can vary between 1 and 10. We will call these "job bullet points".  





IMPORTANT CONSTRAINTS:
- Keep it concise - prioritize relevance over length
- Remove or minimize irrelevant information
- Focus on making changes to the Experience, Skills, and Summary sections.  Also adapt the headline.
- Use bullet points for readability
- Maintain proper markdown structure
- Focus on impact and results
- Do not modify the Education section
- PRESERVE all section separators (*** horizontal rules) from the original resume exactly as they appear

CRITICAL RULES FOR SKILLS:
- ONLY add skills that are EXPLICITLY listed in the suggestions provided
- DO NOT add any skills that are not in the approved suggestions list
- DO NOT infer or assume additional skills should be added
- If a skill is not in the suggestions, it must NOT appear in the modified resume unless it was already in the original resume

GUIDANCE FOR SUMMARY SECTION:
- Craft a summary that bests aligns with the stated job description, emphasizing relevant qualifications and incorporating key responsibilities and skills from the job description.  Ensure each bullet point best describes the action taken and the result achieved.

GUIDANCE FOR EXPERIENCES SECTION:
- Polish the description of the three most recent positions to showcase how the experience best aligns with the requirements of the role.

CRITICAL RULES FOR EXPERIENCE SECTION (ABSOLUTELY NON-NEGOTIABLE):
- ALWAYS preserve the backslash "\" at the end of job metadata (Row 1). This is MANDATORY.
- The job headline (Row 2 in italics) MUST appear on the very next line after job metadata with NO blank lines in between.
- The correct format is: **Title** | **Company** | Location | *Dates*\ (note the backslash at end)
                          *Job headline in italics immediately on next line*
- **NEVER REMOVE THE JOB HEADLINE UNDER ANY CIRCUMSTANCES** - even if you remove all job bullet points, the job headline MUST remain. This is the highest priority rule.
- DO NOT insert blank lines between job metadata and job headline - they must be consecutive lines.
- Every job entry MUST have: (1) job metadata line ending with \, (2) job headline in italics on the next line, (3) optional bullet points. The job headline is NEVER optional.

FORMATTING REQUIREMENTS:
- Each job entry MUST be on its own separate line
- Use CONSISTENT formatting: **Job Title** | <span style="color: #1a73e8;">**Company**</span> | Location | *Dates*
- Include ONE blank line after each job entry (standard markdown, not <br> tags)
- Never combine multiple jobs on the same line
- Do NOT use HTML <br> tags - use standard markdown blank lines only.
- Maintain proper markdown structure with clear line breaks

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

Return the complete modified resume in markdown format. Maintain the structure but apply all suggestions while keeping it concise and focused on relevance to the job."""

        try:
            modified_resume = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5  # Lower temperature for more consistent output
            )

            # Clean up the response
            modified_resume = self._clean_resume(modified_resume)

            # Validate and fix structure
            validation_result = self.validator.validate_and_fix(
                resume=modified_resume,
                original_resume=original_resume
            )

            # Log any issues found
            if validation_result["issues_found"]:
                print("\n⚠️  Structure validation found issues:")
                for issue in validation_result["issues_found"]:
                    print(f"   - {issue}")

            # Log fixes applied
            if validation_result["fixes_applied"]:
                print("\n✓ Structure fixes applied:")
                for fix in validation_result["fixes_applied"]:
                    print(f"   - {fix}")

            # Return the fixed resume
            return validation_result["fixed_resume"]

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
