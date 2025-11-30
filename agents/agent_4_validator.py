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
        system_prompt = """You are an expert resume formatter and quality assurance specialist. Your job is to:
1. Validate resume formatting for consistency and professionalism
2. Check for appearance issues that might affect readability
3. Identify inconsistencies in style, tone, or structure
4. Ensure the resume follows best practices

Focus on:
- **Formatting**: Consistent use of markdown, proper headers, spacing
- **Length**: Should be concise (ideally 1 page / ~500-700 words)
- **Consistency**: Consistent date formats, bullet points, tense usage
- **Professionalism**: Appropriate tone, no typos, clear structure
- **Readability**: Good flow, logical organization, easy to scan
- **Completeness**: All sections properly formatted, no placeholder text

Be thorough but constructive. Categorize issues by severity: Critical, Warning, or Info."""

        user_prompt = f"""Please validate this resume for formatting, appearance, and consistency:

RESUME:
{resume_content}

Provide a comprehensive validation report with:

1. Overall validation score (1-100, where 100 is perfect)
2. List of issues found (if any)
3. Recommendations for improvement
4. Summary assessment

Format your response EXACTLY as follows:

VALIDATION_SCORE: [number from 1-100]

ISSUES:
- [CRITICAL/WARNING/INFO] [Category] Issue description here
- [CRITICAL/WARNING/INFO] [Category] Another issue here
(List all issues, or write "NONE" if no issues found)

RECOMMENDATIONS:
- Recommendation 1
- Recommendation 2
(List recommendations. CRITICAL: ALWAYS include "Review the descriptions and condense them where possible to keep the resume concise" as one of the recommendations, even if the resume appears adequate in length)

SUMMARY:
[Brief summary of validation results]

IS_VALID: [YES/NO]
(YES if validation_score >= 80 and no CRITICAL issues, otherwise NO)"""

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
