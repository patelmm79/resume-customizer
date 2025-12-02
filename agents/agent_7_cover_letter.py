"""Agent 7: Cover Letter Generator."""
from typing import Dict
from utils.agent_helper import get_agent_llm_client


class CoverLetterAgent:
    """Agent that generates tailored cover letters based on resume and job description."""

    def __init__(self):
        """Initialize the cover letter agent."""
        self.client = get_agent_llm_client()

    def generate_cover_letter(
        self,
        resume_content: str,
        job_description: str
    ) -> Dict:
        """
        Generate a tailored cover letter based on the resume and job description.

        Args:
            resume_content: The optimized resume in markdown format
            job_description: The job description text

        Returns:
            Dictionary containing:
                - cover_letter: str (The full cover letter in markdown format)
                - summary: str (Brief summary of the cover letter approach)
        """
        system_prompt = """You are an expert cover letter writer with extensive experience in career coaching and professional communication. Your job is to:

1. Analyze the resume and job description
2. Write a compelling, personalized cover letter that:
   - Highlights the candidate's most relevant qualifications
   - Addresses key requirements from the job description
   - Tells a cohesive story about the candidate's career
   - Shows enthusiasm and cultural fit
   - Is professional yet personable
   - Is concise (3-4 paragraphs, ~250-350 words)

Cover Letter Best Practices:
- Start with a strong opening that grabs attention
- Connect your experience directly to the role's requirements
- Include 2-3 specific achievements with quantifiable results
- Demonstrate knowledge of the company/role
- Show personality and genuine interest
- End with a clear call to action
- Avoid clichés and generic statements
- Don't simply repeat the resume - add context and narrative

Format Guidelines:
- Use proper business letter format
- Include [Your Name], [Your Email], [Your Phone] placeholders at the top
- Include [Date] placeholder
- Include [Hiring Manager's Name] and [Company Name] placeholders
- Use markdown formatting for structure
- Professional but warm tone"""

        user_prompt = f"""Generate a tailored cover letter for this candidate based on their resume and the target job description.

RESUME:
{resume_content}

JOB DESCRIPTION:
{job_description}

Please provide:
1. A complete, professional cover letter in markdown format
2. A brief summary of your approach and key points emphasized

Format your response EXACTLY as follows:

COVER_LETTER:
[Your Name]
[Your Email] | [Your Phone]
[Your LinkedIn] (optional)

[Date]

[Hiring Manager's Name]
[Company Name]
[Company Address]

Dear [Hiring Manager's Name],

[Opening paragraph - grab attention and state the position]

[Body paragraph 1 - highlight relevant experience and achievements]

[Body paragraph 2 - demonstrate fit and enthusiasm]

[Closing paragraph - call to action]

Sincerely,
[Your Name]

SUMMARY:
[Brief explanation of the approach taken, key points emphasized, and why this letter is effective for this specific role]

IMPORTANT:
- Make the cover letter specific to this job, not generic
- Include 2-3 concrete achievements with metrics from the resume
- Show enthusiasm without being over the top
- Keep it concise - aim for 250-350 words
- Use a professional but personable tone"""

        # Invoke the LLM
        content = self.client.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7
        )

        # Debug: Print content length
        print(f"[DEBUG] Cover letter response length: {len(content) if content else 0}")

        # Extract cover letter and summary
        cover_letter = ""
        summary = ""

        try:
            if "COVER_LETTER:" in content:
                parts = content.split("COVER_LETTER:", 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    if "SUMMARY:" in remaining:
                        letter_parts = remaining.split("SUMMARY:", 1)
                        cover_letter = letter_parts[0].strip()
                        summary = letter_parts[1].strip()
                    else:
                        cover_letter = remaining.strip()
                        summary = "Generated a tailored cover letter highlighting key qualifications and achievements."
            else:
                # Fallback: use entire content as cover letter
                cover_letter = content.strip()
                summary = "Generated a tailored cover letter highlighting key qualifications and achievements."
        except Exception as e:
            # Fallback to raw content
            cover_letter = content.strip() if content else ""
            summary = f"Cover letter generated (parsing encountered an issue: {str(e)})"

        # Final validation
        if not cover_letter:
            print(f"[ERROR] Cover letter is empty! Raw content preview: {content[:200] if content else 'None'}")
            # Use raw content as last resort
            cover_letter = content if content else "Error: No content generated"

        print(f"[DEBUG] Final cover letter length: {len(cover_letter)}")

        return {
            "cover_letter": cover_letter,
            "summary": summary
        }

    def revise_cover_letter(
        self,
        original_cover_letter: str,
        reviewer_feedback: Dict,
        resume_content: str,
        job_description: str,
        user_feedback: str = None
    ) -> Dict:
        """
        Revise a cover letter based on reviewer feedback and optional user feedback.

        Args:
            original_cover_letter: The original cover letter to revise
            reviewer_feedback: Feedback from Agent 8 (reviewer)
            resume_content: The resume for context
            job_description: The job description for context
            user_feedback: Optional additional feedback from the user

        Returns:
            Dictionary containing:
                - cover_letter: str (The revised cover letter)
                - revision_notes: str (What was changed and why)
        """
        system_prompt = """You are an expert cover letter writer revising a cover letter based on professional feedback.

Your job is to:
1. Carefully read and understand all feedback provided
2. Revise the cover letter to address ALL critical and content issues
3. Incorporate suggested improvements for minor issues where appropriate
4. Preserve the strengths that were identified
5. Maintain the professional, personable tone
6. Keep the letter concise (3-4 paragraphs, 250-350 words)

Be thorough but efficient in your revisions. Every piece of feedback should be considered and addressed."""

        feedback_summary = f"""
REVIEWER FEEDBACK:

Overall Assessment: {reviewer_feedback.get('overall_assessment', 'N/A')}

CRITICAL ISSUES (Must fix):
{self._format_issues(reviewer_feedback.get('critical_issues', []))}

CONTENT ISSUES (Should fix):
{self._format_issues(reviewer_feedback.get('content_issues', []))}

MINOR ISSUES (Nice to fix):
{self._format_issues(reviewer_feedback.get('minor_issues', []))}

STRENGTHS TO PRESERVE:
{chr(10).join(f"- {s}" for s in reviewer_feedback.get('strengths', []))}
"""

        user_feedback_section = ""
        if user_feedback and user_feedback.strip():
            user_feedback_section = f"""

USER FEEDBACK (Additional instructions from the candidate):
{user_feedback}
"""

        user_prompt = f"""Revise the following cover letter based on the feedback provided.

ORIGINAL COVER LETTER:
{original_cover_letter}

{feedback_summary}
{user_feedback_section}

RESUME (for context):
{resume_content}

JOB DESCRIPTION (for context):
{job_description}

Please provide:
1. The complete REVISED cover letter (maintaining the same format structure)
2. Brief notes on what you changed and why

Format your response EXACTLY as follows:

REVISED_COVER_LETTER:
[Full revised cover letter here]

REVISION_NOTES:
[Bullet points explaining the key changes you made and which feedback they address]

IMPORTANT:
- Address ALL critical issues completely
- Address ALL content issues to the best of your ability
- Preserve the identified strengths
- Fix any dates, placeholders, or factual errors
- Ensure the letter is professional, compelling, and ready to send
- Keep it concise and impactful"""

        # Invoke the LLM
        content = self.client.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7
        )

        # Extract revised letter and notes
        revised_letter = ""
        revision_notes = ""

        try:
            if "REVISED_COVER_LETTER:" in content:
                parts = content.split("REVISED_COVER_LETTER:", 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    if "REVISION_NOTES:" in remaining:
                        letter_parts = remaining.split("REVISION_NOTES:", 1)
                        revised_letter = letter_parts[0].strip()
                        revision_notes = letter_parts[1].strip()
                    else:
                        revised_letter = remaining.strip()
                        revision_notes = "Cover letter revised based on feedback."
            else:
                # Fallback: use entire content as revised letter
                revised_letter = content.strip()
                revision_notes = "Cover letter revised based on feedback."
        except Exception as e:
            revised_letter = content.strip() if content else original_cover_letter
            revision_notes = f"Revision completed (parsing encountered an issue: {str(e)})"

        if not revised_letter:
            print(f"[ERROR] Revised cover letter is empty! Using original.")
            revised_letter = original_cover_letter
            revision_notes = "Error during revision - original letter preserved"

        return {
            "cover_letter": revised_letter,
            "revision_notes": revision_notes
        }

    @staticmethod
    def _format_issues(issues: list) -> str:
        """Format a list of issues for display."""
        if not issues:
            return "None"

        formatted = []
        for i, issue in enumerate(issues, 1):
            if isinstance(issue, dict):
                formatted.append(
                    f"{i}. {issue.get('issue', 'N/A')}\n"
                    f"   Location: {issue.get('location', 'N/A')}\n"
                    f"   Fix: {issue.get('fix', 'N/A')}"
                )
            else:
                formatted.append(f"{i}. {issue}")
        return "\n".join(formatted)
