"""Agent 4: Resume Formatting Validator."""
from typing import Dict, List
from utils.agent_helper import get_agent_llm_client


class ResumeValidatorAgent:
    """Agent that validates resume formatting, appearance, and consistency."""

    def __init__(self):
        """Initialize the validator agent."""
        self.client = get_agent_llm_client()

    def validate_resume(
        self,
        resume_content: str
    ) -> Dict:
        """
        Validate resume formatting, appearance, and consistency.

        Args:
            resume_content: Resume in markdown format

        Returns:
            Dictionary containing:
                - is_valid: bool (True if passes all checks)
                - validation_score: int (1-100)
                - issues: List[Dict] with 'severity', 'category', 'description'
                - recommendations: List[str]
                - summary: str
        """
        system_prompt = """You are an expert resume formatting specialist. Your ONLY job is to:
1. Check visual formatting and presentation
2. Ensure consistency in styling
3. Provide formatting recommendations

Focus ONLY on:
- **Markdown Formatting**: Proper use of headers (# ## ###), bold, italics
- **Visual Consistency**: Consistent date formats (e.g., "Jan 2020 - Present" vs "2020-01 to now")
- **Bullet Point Style**: Consistent bullet formatting throughout
- **Section Structure**: Proper hierarchy and organization of sections
- **Spacing**: Appropriate use of line breaks and whitespace
- **Typography**: Consistent capitalization, punctuation

DO NOT:
- Check content quality or relevance (that's handled elsewhere)
- Comment on resume length (optimization handles this)
- Suggest removing content
- Analyze job fit or skills

You are strictly a formatting QA checker. Be thorough but focus only on visual presentation."""

        user_prompt = f"""Please check this resume ONLY for formatting and visual presentation issues:

RESUME:
{resume_content}

Focus on formatting ONLY - ignore content quality, length, or relevance.

Provide a formatting validation report:

1. Overall formatting score (1-100, where 100 is perfect formatting)
2. List of formatting issues found (if any)
3. Formatting recommendations
4. Summary

Format your response EXACTLY as follows:

VALIDATION_SCORE: [number from 1-100]

ISSUES:
- [CRITICAL/WARNING/INFO] [Category] Issue description here
- [CRITICAL/WARNING/INFO] [Category] Another issue here
(List ONLY formatting issues, or write "NONE" if formatting is perfect)

Categories should be: Markdown, Date Format, Bullet Style, Section Structure, Spacing, Typography

RECOMMENDATIONS:
- Formatting recommendation 1
- Formatting recommendation 2
(List ONLY formatting recommendations. Do NOT suggest content changes or length reduction)

SUMMARY:
[Brief summary of formatting quality]

IS_VALID: [YES/NO]
(YES if validation_score >= 80 and no CRITICAL formatting issues, otherwise NO)"""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4  # Lower temperature for consistent validation
            )

            return self._parse_response(response)

        except Exception as e:
            raise Exception(f"Validation failed: {str(e)}")

    def _parse_response(self, response: str) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response

        Returns:
            Structured dictionary with validation results
        """
        lines = response.strip().split('\n')

        validation_score = 80  # Default
        issues = []
        recommendations = []
        summary = ""
        is_valid = True
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("VALIDATION_SCORE:"):
                score_text = line.replace("VALIDATION_SCORE:", "").strip()
                try:
                    validation_score = int(score_text)
                except ValueError:
                    import re
                    match = re.search(r'\d+', score_text)
                    if match:
                        validation_score = int(match.group())
                current_section = "score"

            elif line.startswith("ISSUES:"):
                current_section = "issues"

            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"

            elif line.startswith("SUMMARY:"):
                current_section = "summary"

            elif line.startswith("IS_VALID:"):
                valid_text = line.replace("IS_VALID:", "").strip().upper()
                is_valid = "YES" in valid_text
                current_section = "is_valid"

            elif line and current_section == "issues" and line.startswith("-"):
                issue_text = line[1:].strip()

                # Skip "NONE" placeholder
                if issue_text.upper() == "NONE":
                    continue

                # Parse severity and category
                severity = "INFO"
                category = "General"
                description = issue_text

                # Extract [SEVERITY] [Category]
                import re
                severity_match = re.match(r'\[(CRITICAL|WARNING|INFO)\]\s*\[([^\]]+)\]\s*(.+)', issue_text, re.IGNORECASE)
                if severity_match:
                    severity = severity_match.group(1).upper()
                    category = severity_match.group(2).strip()
                    description = severity_match.group(3).strip()

                issues.append({
                    "severity": severity,
                    "category": category,
                    "description": description
                })

            elif line and current_section == "recommendations" and line.startswith("-"):
                rec_text = line[1:].strip()
                if rec_text.upper() != "NONE":
                    recommendations.append(rec_text)

            elif line and current_section == "summary" and not line.startswith(("ISSUES:", "RECOMMENDATIONS:", "VALIDATION_SCORE:", "IS_VALID:")):
                summary += line + " "

        # Ensure validation score is in range
        if validation_score < 1:
            validation_score = 1
        elif validation_score > 100:
            validation_score = 100

        # Check for critical issues
        has_critical = any(issue["severity"] == "CRITICAL" for issue in issues)
        if has_critical or validation_score < 80:
            is_valid = False

        return {
            "validation_score": validation_score,
            "is_valid": is_valid,
            "issues": issues,
            "recommendations": recommendations,
            "summary": summary.strip() if summary else "Validation completed.",
            "critical_count": sum(1 for i in issues if i["severity"] == "CRITICAL"),
            "warning_count": sum(1 for i in issues if i["severity"] == "WARNING"),
            "info_count": sum(1 for i in issues if i["severity"] == "INFO")
        }
