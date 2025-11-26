"""Agent 5: Resume Length Optimizer."""
from typing import Dict
from utils.agent_helper import get_agent_llm_client
from utils.resume_validator import ResumeStructureValidator


class ResumeOptimizerAgent:
    """Agent that optimizes resume length while maintaining score."""

    def __init__(self):
        """Initialize the optimizer agent."""
        self.client = get_agent_llm_client()
        self.validator = ResumeStructureValidator()

    def optimize_resume(
        self,
        resume_content: str,
        job_description: str,
        current_score: int
    ) -> Dict:
        """
        Optimize resume to be as concise as possible without impacting score.

        Args:
            resume_content: Resume in markdown format
            job_description: Job description for context
            current_score: The current compatibility score to maintain

        Returns:
            Dictionary containing:
                - optimized_resume: str (optimized resume content)
                - word_count_before: int
                - word_count_after: int
                - optimization_summary: str
                - changes_made: List[str]
        """
        system_prompt = """You are an expert resume optimizer specializing in concise, impactful writing. Your job is to:
1. Make the resume as concise as possible while maintaining its effectiveness
2. Remove redundancy, wordiness, and unnecessary details
3. Keep all critical information that contributes to the job match
4. Aim for 1 page (approximately 500-700 words maximum)
5. Maintain or improve the compatibility score.
6. PRESERVE all section separators (*** horizontal rules) from the original resume.  Do not ask to remove or change these.
7. In the Experience section, PRESERVE the first line under each role if the line is marked in *italics*

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


Optimization strategies:
- Remove redundant phrases and filler words
- Combine similar bullet points
- Use stronger, more concise action verbs
- Remove less relevant experiences if space is tight
- Consolidate skills into efficient lists
- Ensure every word adds value
- Remove all skills that are minimally relevant to the role. 
- If individual skills are similar, only keep the skill most relevant to the job description.
- Eliminate job bullet points under all roles before the most recent 4 roles, unless they are directly relevant to the role.  However, DO NOT modify job headline.  
- For certifications, keep all certifications for AWS and Google Cloud in all cases.  For other certifications, keep only those certifications that are directly relevant to the role.

CRITICAL:
- Do not remove information that is directly relevant to the job description. The goal is conciseness without sacrificing match quality.
- Each job should have no more than the top 5 to 6 bullet points most relevant to the position. All other need to be removed.
- **ABSOLUTE REQUIREMENT**: NEVER remove or modify job headlines (the italicized descriptions after job metadata). Job headlines MUST be preserved even when all bullet points are removed. This is the highest priority rule that overrides all space optimization concerns.
- DO NOT add spaces between job metadata and job headline.


FORMATTING REQUIREMENTS:
- Each job entry MUST be on its own line, even older positions without bullet points
- Use CONSISTENT formatting for ALL jobs: "**Job Title** | <span style="color: #1a73e8;">**Company**</span> | Location | *Dates*\"
- Each job entry should have ONE blank line before and after it (use standard markdown, not <br> tags)
- Never combine multiple jobs on the same line
- Do NOT use HTML <br> tags - use standard markdown blank lines only. 
- Maintain proper markdown structure with line breaks between all job entries
- Do NOT change formatting of job headline to add any line break in between.

CRITICAL RULES FOR EXPERIENCE SECTION (ABSOLUTELY NON-NEGOTIABLE):
- ALWAYS preserve the backslash "\" at the end of job metadata (Row 1). This is MANDATORY.
- The job headline (Row 2 in italics) MUST appear on the very next line after job metadata with NO blank lines in between.
- The correct format is: **Title** | **Company** | Location | *Dates*\ (note the backslash at end)
                          *Job headline in italics immediately on next line*
- **NEVER REMOVE THE JOB HEADLINE UNDER ANY CIRCUMSTANCES** - even if you remove all job bullet points, the job headline MUST remain. This is the highest priority rule.
- DO NOT insert blank lines between job metadata and job headline - they must be consecutive lines.
- Every job entry MUST have: (1) job metadata line ending with \, (2) job headline in italics on the next line, (3) optional bullet points. The job headline is NEVER optional.


PAGE LAYOUT OPTIMIZATION:
- Limit each job (with bullets) to maximum 5-6 bullet points to help prevent page splits
- For recent jobs, keep bullet lists concise and focused on most relevant points
- Organize content to minimize section splits across pages:
  * Skills section should be concise (combine similar skills)
  * Education/Certifications should be brief, one-liners when possible
- Aim for natural content breaks that align with page boundaries
"""

        user_prompt = f"""Please optimize this resume to be as concise as possible while maintaining a compatibility score of {current_score}/100 with the job description.

CURRENT RESUME:
{resume_content}

JOB DESCRIPTION:
{job_description}

TARGET: Ideally 1 page (500-700 words). Current resume should be shortened without losing relevance.

**CRITICAL REMINDER**: When optimizing the Experience section, you MUST preserve the job headline (italicized description line) for EVERY job entry, even if you remove all bullet points. Job headlines are NEVER optional and MUST NOT be removed under any circumstances.

Please format your response EXACTLY as follows:

OPTIMIZED_RESUME:
[Your optimized resume in markdown format here]

OPTIMIZATION_SUMMARY:
[Brief summary of what was optimized and why]

CHANGES_MADE:
- Change 1 description
- Change 2 description
- Change 3 description
(List all optimization changes made)

Ensure the optimized resume maintains all key information relevant to the job while being maximally concise."""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4  # Lower temperature for consistent optimization
            )

            result = self._parse_response(response, resume_content)

            # Validate and fix structure of optimized resume
            validation_result = self.validator.validate_and_fix(
                resume=result["optimized_resume"],
                original_resume=resume_content
            )

            # Log any issues found
            if validation_result["issues_found"]:
                print("\n⚠️  Structure validation found issues in optimized resume:")
                for issue in validation_result["issues_found"]:
                    print(f"   - {issue}")

            # Log fixes applied
            if validation_result["fixes_applied"]:
                print("\n✓ Structure fixes applied to optimized resume:")
                for fix in validation_result["fixes_applied"]:
                    print(f"   - {fix}")

                # Add fixes to changes_made list
                result["changes_made"].extend([
                    f"[Auto-fix] {fix}" for fix in validation_result["fixes_applied"]
                ])

            # Update the optimized resume with fixed version
            result["optimized_resume"] = validation_result["fixed_resume"]

            # Recalculate word count after fixes
            result["word_count_after"] = len(validation_result["fixed_resume"].split())
            result["words_removed"] = result["word_count_before"] - result["word_count_after"]

            return result

        except Exception as e:
            raise Exception(f"Optimization failed: {str(e)}")

    def _parse_response(self, response: str, original_resume: str) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response
            original_resume: Original resume for comparison

        Returns:
            Structured dictionary with optimization results
        """
        lines = response.strip().split('\n')

        optimized_resume = []
        optimization_summary = ""
        changes_made = []
        current_section = None

        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith("OPTIMIZED_RESUME:"):
                current_section = "optimized_resume"
                continue

            elif stripped_line.startswith("OPTIMIZATION_SUMMARY:"):
                current_section = "optimization_summary"
                continue

            elif stripped_line.startswith("CHANGES_MADE:"):
                current_section = "changes_made"
                continue

            # Collect content for each section
            if current_section == "optimized_resume":
                if not stripped_line.startswith(("OPTIMIZATION_SUMMARY:", "CHANGES_MADE:")):
                    optimized_resume.append(line)

            elif current_section == "optimization_summary":
                if not stripped_line.startswith("CHANGES_MADE:") and stripped_line:
                    optimization_summary += stripped_line + " "

            elif current_section == "changes_made":
                if stripped_line.startswith("-"):
                    change_text = stripped_line[1:].strip()
                    changes_made.append(change_text)

        # Join optimized resume
        optimized_resume_text = '\n'.join(optimized_resume).strip()

        # Clean up markdown code blocks if present
        if optimized_resume_text.startswith("```"):
            lines = optimized_resume_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            optimized_resume_text = '\n'.join(lines).strip()

        # Calculate word counts
        word_count_before = len(original_resume.split())
        word_count_after = len(optimized_resume_text.split())

        return {
            "optimized_resume": optimized_resume_text,
            "word_count_before": word_count_before,
            "word_count_after": word_count_after,
            "words_removed": word_count_before - word_count_after,
            "optimization_summary": optimization_summary.strip() if optimization_summary else "Resume optimized for length.",
            "changes_made": changes_made if changes_made else ["Resume condensed while maintaining key information"]
        }
