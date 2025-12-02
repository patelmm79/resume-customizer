"""Agent 5: Resume Length Optimizer."""
from typing import Dict, List
from utils.agent_helper import get_agent_llm_client
from utils.resume_validator import ResumeStructureValidator
from utils.resume_standards import get_optimization_prompt_prefix


class ResumeOptimizerAgent:
    """Agent that optimizes resume length while maintaining score."""

    def __init__(self):
        """Initialize the optimizer agent."""
        self.client = get_agent_llm_client()
        self.validator = ResumeStructureValidator()

    def suggest_optimizations(
        self,
        resume_content: str,
        job_description: str,
        current_score: int
    ) -> Dict:
        """
        Suggest optimizations to make resume more concise without impacting score.

        Args:
            resume_content: Resume in markdown format
            job_description: Job description for context
            current_score: The current compatibility score to maintain

        Returns:
            Dictionary containing:
                - suggestions: List[Dict] with optimization suggestions
                - current_word_count: int
                - analysis: str (explanation of optimization opportunities)
        """
        # Get centralized standards
        standards_prefix = get_optimization_prompt_prefix()

        system_prompt = f"""{standards_prefix}

You are analyzing a resume to suggest optimizations. Your goal is to identify specific changes that would make the resume more concise without losing relevance or lowering the job match score.

IMPORTANT: Do NOT make changes yourself. Only SUGGEST what could be optimized."""

        user_prompt = f"""Analyze this resume and suggest specific optimizations to make it more concise while maintaining a compatibility score of {current_score}/100.

CURRENT RESUME ({len(resume_content.split())} words):
{resume_content}

JOB DESCRIPTION:
{job_description}

TARGET: 500-700 words (1 page)

Please identify optimization opportunities and format your response EXACTLY as follows:

ANALYSIS:
[Brief analysis of optimization opportunities - which sections are too verbose, what could be condensed, etc.]

SUGGESTIONS:
- [CATEGORY: Experience] [DESCRIPTION: Remove bullets 4-6 from role X (2015-2017) - older and less relevant] [LOCATION: Job title at Company]
- [CATEGORY: Skills] [DESCRIPTION: Remove redundant skills: X, Y, Z - not mentioned in job description] [LOCATION: Skills section]
- [CATEGORY: Experience] [DESCRIPTION: Condense bullet 2 in role Y - too wordy, can reduce from 25 to 15 words] [LOCATION: Job title at Company]
- [CATEGORY: Summary] [DESCRIPTION: Tighten summary - reduce from 80 to 50 words by removing redundant phrases] [LOCATION: Summary section]

Format rules:
- Each suggestion must have CATEGORY, DESCRIPTION, and LOCATION tags
- Be specific about what to change and where
- Focus on removing/condensing content, not adding
- Prioritize older, less relevant content
- NEVER suggest removing job headlines
- Each suggestion should be independently selectable"""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4
            )

            return self._parse_suggestions_response(response, resume_content)

        except Exception as e:
            raise Exception(f"Optimization analysis failed: {str(e)}")

    def _parse_suggestions_response(self, response: str, resume_content: str) -> Dict:
        """
        Parse suggestions response into structured data.

        Args:
            response: Raw LLM response with suggestions
            resume_content: Original resume

        Returns:
            Dictionary with suggestions and analysis
        """
        import re

        analysis = ""
        suggestions = []
        current_section = None

        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith("ANALYSIS:"):
                current_section = "analysis"
                analysis_text = line.replace("ANALYSIS:", "").strip()
                if analysis_text:
                    analysis = analysis_text
                continue

            elif line.startswith("SUGGESTIONS:"):
                current_section = "suggestions"
                continue

            if current_section == "analysis" and line:
                analysis += "\n" + line

            elif current_section == "suggestions" and line.startswith("-"):
                # Parse suggestion line
                suggestion_text = line[1:].strip()

                category = "General"
                description = suggestion_text
                location = ""

                # Extract CATEGORY
                if "[CATEGORY:" in suggestion_text:
                    cat_match = re.search(r'\[CATEGORY:\s*([^\]]+)\]', suggestion_text)
                    if cat_match:
                        category = cat_match.group(1).strip()

                # Extract DESCRIPTION
                if "[DESCRIPTION:" in suggestion_text:
                    desc_match = re.search(r'\[DESCRIPTION:\s*([^\]]+)\]', suggestion_text)
                    if desc_match:
                        description = desc_match.group(1).strip()

                # Extract LOCATION
                if "[LOCATION:" in suggestion_text:
                    loc_match = re.search(r'\[LOCATION:\s*([^\]]+)\]', suggestion_text)
                    if loc_match:
                        location = loc_match.group(1).strip()

                suggestions.append({
                    "id": len(suggestions),
                    "text": description,
                    "category": category,
                    "location": location,
                    "selected": True  # Default to selected
                })

        return {
            "suggestions": suggestions,
            "analysis": analysis.strip(),
            "current_word_count": len(resume_content.split())
        }

    def apply_optimizations(
        self,
        resume_content: str,
        suggestions: List[Dict],
        job_description: str
    ) -> str:
        """
        Apply selected optimization suggestions to the resume.

        Args:
            resume_content: Current resume
            suggestions: List of optimization suggestions (only selected ones will be applied)
            job_description: Job description for context

        Returns:
            Optimized resume
        """
        selected_suggestions = [s for s in suggestions if s.get("selected", False)]

        if not selected_suggestions:
            return resume_content

        # Get centralized standards
        standards_prefix = get_optimization_prompt_prefix()

        system_prompt = f"""{standards_prefix}

Apply the selected optimization suggestions to make the resume more concise."""

        suggestions_text = "\n".join([
            f"- [{s['category']}] {s['text']}" + (f" (Location: {s['location']})" if s.get('location') else "")
            for s in selected_suggestions
        ])

        user_prompt = f"""Apply these optimization suggestions to the resume:

SELECTED OPTIMIZATIONS:
{suggestions_text}

CURRENT RESUME:
{resume_content}

Return ONLY the optimized resume in markdown format. Apply the selected optimizations while:
- Maintaining all formatting standards
- Preserving job headlines
- Keeping all backslashes in metadata lines
- Not removing content that wasn't suggested for removal"""

        try:
            optimized_resume = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )

            # Validate and fix structure
            validation_result = self.validator.validate_and_fix(
                resume=optimized_resume,
                original_resume=resume_content
            )

            if validation_result["fixes_applied"]:
                print("\n✓ Structure fixes applied:")
                for fix in validation_result["fixes_applied"]:
                    print(f"   - {fix}")

            return validation_result["fixed_resume"]

        except Exception as e:
            raise Exception(f"Failed to apply optimizations: {str(e)}")

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
