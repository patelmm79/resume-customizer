"""Agent 5: Resume Length Optimizer."""
from typing import Dict, List
from utils.agent_helper import get_agent_llm_client
from utils.resume_standards import get_optimization_prompt_prefix


class ResumeOptimizerAgent:
    """Agent that optimizes resume length while maintaining score."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the optimizer agent."""
        self.client = get_agent_llm_client()
        self.debug_mode = debug_mode

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

CRITICAL RULES:
1. Do NOT make changes yourself. Only SUGGEST what could be optimized.
2. NEVER EVER suggest removing entire job entries, roles, or positions from the Experience section.
3. You can ONLY suggest removing individual bullet points within jobs, never the job itself.
4. Job titles, company names, and date ranges must ALWAYS remain intact.
5. Focus on trimming bullet points from older roles (5+ years ago) to save space."""

        user_prompt = f"""Analyze this resume and suggest specific optimizations to make it more concise while maintaining a compatibility score of {current_score}/100.

CURRENT RESUME ({len(resume_content.split())} words):
{resume_content}

JOB DESCRIPTION:
{job_description}

TARGET: 500-700 words (1 page)

CRITICAL OPTIMIZATION PRIORITIES:
1. **Older Roles (5+ years ago)**: ALWAYS suggest removing less relevant bullet points from older positions
   - Keep only 2-3 most impactful bullets for older roles
   - Remove bullets that don't directly relate to the target job
   - ONLY remove individual bullet points, NEVER the job entry itself

2. **Redundancy**: Remove skills or phrases already covered elsewhere

3. **Wordiness**: Condense verbose descriptions

❌ ABSOLUTELY FORBIDDEN - NEVER DO THIS:
- NEVER suggest removing an entire job/role/position from Experience section
- NEVER suggest removing job titles (e.g., "Software Engineer")
- NEVER suggest removing company names (e.g., "Tech Corp")
- NEVER suggest removing date ranges (e.g., "2015-2017")
- NEVER say things like "Remove this role", "Remove this position", "Remove this job"

✅ WHAT YOU CAN SUGGEST:
- Remove specific bullet points within a role (e.g., "Remove bullet 3 from Senior Engineer role")
- Condense bullet points to be more concise
- Remove redundant skills or phrases
- Tighten summaries

Every job entry MUST remain with its title, company, and dates intact. You can only suggest removing or condensing the bullet points underneath.

Please provide your response in VALID JSON format ONLY (no markdown, no code blocks, just pure JSON):

{{
  "analysis": "Brief analysis of optimization opportunities - which sections are too verbose, what could be condensed, etc. Specifically mention older roles where BULLET POINTS should be trimmed.",
  "suggestions": [
    {{
      "category": "Experience",
      "description": "Remove bullets 4-6 from role X (2015-2017) - older and less relevant to target role",
      "location": "Job title at Company"
    }},
    {{
      "category": "Experience",
      "description": "Remove bullet 3 from role Y (2016-2018) - outdated technology not in job description",
      "location": "Job title at Company"
    }},
    {{
      "category": "Skills",
      "description": "Remove redundant skills: X, Y, Z - not mentioned in job description",
      "location": "Skills section"
    }},
    {{
      "category": "Experience",
      "description": "Condense bullet 2 in role Z - too wordy, can reduce from 25 to 15 words",
      "location": "Job title at Company"
    }}
  ]
}}

CRITICAL:
- Return ONLY valid JSON, no markdown formatting, no ```json code blocks
- Each suggestion must have category, description, and location fields
- Be specific about WHICH BULLETS to change and where
- Focus on removing/condensing BULLET POINTS ONLY, never entire job entries
- **ALWAYS** suggest bullet point removal for roles 5+ years old
- NEVER suggest removing job headlines (titles, companies, or date ranges)
- NEVER suggest removing entire positions/roles"""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4
            )

            # Debug output (only if debug_mode is enabled)
            if self.debug_mode:
                print(f"\n[Agent5 DEBUG] Response length: {len(response)} chars")
                print(f"[Agent5 DEBUG] First 800 chars:\n{response[:800]}\n")

            parsed_result = self._parse_suggestions_response(response, resume_content)

            if self.debug_mode:
                print(f"[Agent5 DEBUG] Parsed {len(parsed_result['suggestions'])} suggestions")
                if len(parsed_result['suggestions']) == 0:
                    print(f"[Agent5 DEBUG] NO SUGGESTIONS PARSED!")
                    print(f"[Agent5 DEBUG] Checking format markers:")
                    print(f"  - Contains 'ANALYSIS:': {'ANALYSIS:' in response}")
                    print(f"  - Contains '# ANALYSIS': {'# ANALYSIS' in response}")
                    print(f"  - Contains 'SUGGESTIONS:': {'SUGGESTIONS:' in response}")
                    print(f"  - Contains '# SUGGESTIONS': {'# SUGGESTIONS' in response}")
                    print(f"  - Contains '**CATEGORY:': {'**CATEGORY:' in response}")
                    print(f"  - Contains '[CATEGORY:': {'[CATEGORY:' in response}")

            return parsed_result

        except Exception as e:
            raise Exception(f"Optimization analysis failed: {str(e)}")

    def _parse_suggestions_response(self, response: str, resume_content: str) -> Dict:
        """
        Parse suggestions response into structured data.

        Args:
            response: Raw LLM response with suggestions (expected as JSON)
            resume_content: Original resume

        Returns:
            Dictionary with suggestions and analysis
        """
        import json
        import re

        # Clean up response - remove markdown code blocks if present
        cleaned_response = response.strip()

        # Remove ```json and ``` markers if present
        if cleaned_response.startswith("```"):
            # Find first newline after opening ```
            first_newline = cleaned_response.find('\n')
            if first_newline != -1:
                cleaned_response = cleaned_response[first_newline + 1:]

            # Remove closing ```
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3].strip()

        if self.debug_mode:
            print(f"[Agent5 DEBUG] Cleaned response first 500 chars:\n{cleaned_response[:500]}\n")

        try:
            # Parse JSON
            parsed = json.loads(cleaned_response)

            # Extract analysis and suggestions
            analysis = parsed.get("analysis", "")
            raw_suggestions = parsed.get("suggestions", [])

            # Convert to internal format with id and selected fields
            suggestions = []
            for idx, suggestion in enumerate(raw_suggestions):
                suggestions.append({
                    "id": idx,
                    "text": suggestion.get("description", ""),
                    "category": suggestion.get("category", "General"),
                    "location": suggestion.get("location", ""),
                    "selected": True  # Default to selected
                })

            if self.debug_mode:
                print(f"[Agent5 DEBUG] JSON parsed successfully: {len(suggestions)} suggestions")

            return {
                "suggestions": suggestions,
                "analysis": analysis.strip(),
                "current_word_count": len(resume_content.split())
            }

        except json.JSONDecodeError as e:
            if self.debug_mode:
                print(f"[Agent5 DEBUG] JSON parse failed: {str(e)}")
                print(f"[Agent5 DEBUG] Attempting fallback parsing...")

            # Fallback: Try to extract JSON from text
            # Sometimes LLM includes text before/after JSON
            json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    analysis = parsed.get("analysis", "")
                    raw_suggestions = parsed.get("suggestions", [])

                    suggestions = []
                    for idx, suggestion in enumerate(raw_suggestions):
                        suggestions.append({
                            "id": idx,
                            "text": suggestion.get("description", ""),
                            "category": suggestion.get("category", "General"),
                            "location": suggestion.get("location", ""),
                            "selected": True
                        })

                    if self.debug_mode:
                        print(f"[Agent5 DEBUG] Fallback successful: {len(suggestions)} suggestions")

                    return {
                        "suggestions": suggestions,
                        "analysis": analysis.strip(),
                        "current_word_count": len(resume_content.split())
                    }
                except json.JSONDecodeError:
                    pass

            # If all parsing fails, return empty result with error in analysis
            if self.debug_mode:
                print(f"[Agent5 DEBUG] All parsing methods failed")

            return {
                "suggestions": [],
                "analysis": "Failed to parse optimization suggestions. Please try again.",
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
- Not removing content that wasn't suggested for removal

❌ ABSOLUTELY FORBIDDEN - DO NOT TOUCH FORMATTING:
- NEVER change bold formatting (** or <b> tags)
- NEVER change italic formatting (* or <i> tags)
- NEVER change colors (HTML color tags or CSS)
- NEVER change font sizes, styles, or any visual formatting
- NEVER remove user's custom HTML/CSS formatting
- PRESERVE ALL existing formatting EXACTLY as it appears in the original
- Your ONLY job is to apply content optimizations (remove bullets, condense text)
- Formatting changes are STRICTLY FORBIDDEN and handled by a different agent

Return the optimized resume with ALL ORIGINAL FORMATTING PRESERVED EXACTLY. Only apply the content optimizations that were approved."""

        try:
            optimized_resume = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )

            # NO AUTO-FIXES - Return the resume as-is from LLM
            # Agent 4 will validate and report issues only
            return optimized_resume

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
