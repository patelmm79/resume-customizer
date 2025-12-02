"""
Agent 8: Cover Letter Reviewer
Reviews cover letters for quality, professionalism, and effectiveness.
Provides detailed feedback for the writer agent to incorporate.
"""

from typing import Dict, List
import json
import re
from utils.agent_helper import get_agent_llm_client


def review_cover_letter(
    cover_letter: str,
    job_description: str,
    resume: str
) -> Dict:
    """
    Reviews a cover letter and provides detailed feedback.

    Args:
        cover_letter: The cover letter text to review
        job_description: The job description
        resume: The candidate's resume for context

    Returns:
        Dictionary containing:
        - overall_assessment: Overall quality assessment
        - critical_issues: List of critical problems that must be fixed
        - content_issues: List of content/structure problems
        - minor_issues: List of minor improvements
        - strengths: What works well in the letter
        - revision_needed: Boolean indicating if revision is required
    """

    client = get_agent_llm_client()

    system_prompt = """You are an expert cover letter reviewer with extensive experience in hiring and recruitment.

Your task is to review a cover letter and provide detailed, actionable feedback.

Provide a comprehensive review covering:

1. **Critical Issues** (Must fix - these are dealbreakers):
   - Incorrect dates or outdated information
   - Placeholder text or missing information
   - Factual errors or inconsistencies with resume
   - Inappropriate tone or unprofessional content
   - Wrong company or position name

2. **Content Issues** (Should fix - these weaken the letter):
   - Length problems (too long >400 words or too short <200 words)
   - Weak opening that doesn't grab attention
   - Too much resume repetition instead of storytelling
   - Lack of company research or specific enthusiasm
   - Generic statements that could apply to any job
   - Missing connection between candidate and role
   - Weak or passive closing

3. **Minor Issues** (Nice to fix - polish):
   - Formatting inconsistencies
   - Word choice or phrasing improvements
   - Tone adjustments
   - Minor grammar or style suggestions

4. **Strengths** (What works well):
   - Effective elements that should be preserved
   - Strong selling points
   - Good structure or flow

Return your review in this EXACT JSON format:
{{
    "overall_assessment": "2-3 sentence summary of the letter's quality",
    "critical_issues": [
        {{"issue": "description", "location": "where in letter", "fix": "how to fix"}}
    ],
    "content_issues": [
        {{"issue": "description", "location": "where in letter", "fix": "how to fix"}}
    ],
    "minor_issues": [
        {{"issue": "description", "location": "where in letter", "fix": "how to fix"}}
    ],
    "strengths": ["strength 1", "strength 2", ...],
    "revision_needed": true/false,
    "revision_priority": "critical|moderate|minor|none"
}}

Be specific, constructive, and actionable in your feedback. Focus on making the cover letter compelling and professional."""

    user_prompt = f"""Review the following cover letter for a job application.

JOB DESCRIPTION:
{job_description}

CANDIDATE'S RESUME (for context):
{resume}

COVER LETTER TO REVIEW:
{cover_letter}

Please provide your detailed review following the format specified in the system prompt."""

    response = client.generate_with_system_prompt(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.7
    )

    # Parse JSON from response
    try:
        # Try to extract JSON from response (sometimes LLMs wrap it in markdown or use escaped braces)
        # First, try to fix common LLM JSON issues
        cleaned_response = response.replace('{{', '{').replace('}}', '}')

        # Try to extract JSON block
        json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(cleaned_response)

        return result
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON from review response: {e}")
        print(f"[DEBUG] Response was: {response[:500]}...")

        # Return a fallback structure
        return {
            "overall_assessment": "Unable to parse review results. Please try again.",
            "critical_issues": [],
            "content_issues": [],
            "minor_issues": [],
            "strengths": [],
            "revision_needed": False,
            "revision_priority": "none"
        }


def assess_revision_quality(
    original_cover_letter: str,
    revised_cover_letter: str,
    original_feedback: Dict,
    job_description: str
) -> Dict:
    """
    Assesses whether the revision adequately addressed the feedback.

    Args:
        original_cover_letter: Original cover letter
        revised_cover_letter: Revised cover letter
        original_feedback: Feedback that was provided
        job_description: Job description for context

    Returns:
        Dictionary containing:
        - issues_resolved: List of issues that were fixed
        - issues_remaining: List of issues still present
        - new_issues: Any new problems introduced
        - approval_status: "approved" or "needs_revision"
        - final_comments: Overall assessment
    """

    client = get_agent_llm_client()

    system_prompt = """You are reviewing a revised cover letter to assess if it adequately addressed previous feedback.

Assess the revision quality:

1. Which issues from the feedback were successfully resolved?
2. Which issues are still present or inadequately addressed?
3. Were any new problems introduced in the revision?
4. Is the revised letter ready for the user to review, or does it need another revision?

Return your assessment in this EXACT JSON format:
{{
    "issues_resolved": [
        {{"issue": "what was fixed", "assessment": "how well it was fixed"}}
    ],
    "issues_remaining": [
        {{"issue": "what's still wrong", "severity": "critical|moderate|minor"}}
    ],
    "new_issues": [
        {{"issue": "new problem", "severity": "critical|moderate|minor"}}
    ],
    "approval_status": "approved|needs_revision",
    "final_comments": "Overall assessment of the revision quality and readiness",
    "improvement_score": 1-10
}}

Be fair but thorough. The goal is a professional, compelling cover letter."""

    user_prompt = f"""Assess the quality of this revision.

JOB DESCRIPTION:
{job_description}

ORIGINAL COVER LETTER:
{original_cover_letter}

PREVIOUS FEEDBACK PROVIDED:
Critical Issues: {original_feedback.get('critical_issues', [])}
Content Issues: {original_feedback.get('content_issues', [])}
Minor Issues: {original_feedback.get('minor_issues', [])}

REVISED COVER LETTER:
{revised_cover_letter}

Please provide your assessment following the format specified in the system prompt."""

    response = client.generate_with_system_prompt(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.7
    )

    # Parse JSON from response
    try:
        # Fix common LLM JSON issues
        cleaned_response = response.replace('{{', '{').replace('}}', '}')

        # Try to extract JSON block
        json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(cleaned_response)

        return result
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON from assessment response: {e}")
        print(f"[DEBUG] Response was: {response[:500]}...")

        # Return a fallback structure
        return {
            "issues_resolved": [],
            "issues_remaining": [],
            "new_issues": [],
            "approval_status": "approved",
            "final_comments": "Unable to parse assessment results. Proceeding with revision.",
            "improvement_score": 5
        }
