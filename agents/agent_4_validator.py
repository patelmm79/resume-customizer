"""Agent 4: Resume Formatting Validator."""
from typing import Dict, List, Optional
from utils.agent_helper import get_agent_llm_client
from agents.schemas import ValidationSchema
import inspect


class ResumeValidatorAgent:
    """Agent that validates resume formatting, appearance, and consistency."""

    def __init__(self):
        """Initialize the validator agent."""
        self.client = get_agent_llm_client()

    def _get_response_format(self, schema_class) -> Optional[Dict]:
        """Build response_format parameter for structured output."""
        try:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_class.__name__,
                    "schema": schema_class.model_json_schema(),
                    "strict": True,
                },
            }
            print(f"[DEBUG AGENT4] Built response_format for {schema_class.__name__}")
            return response_format
        except Exception as e:
            print(f"[DEBUG AGENT4] Could not build response_format: {e}")
            return None

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

Provide a formatting validation report in JSON format:

{{
  "validation_score": 95,
  "is_valid": true,
  "issues": [
    {{
      "severity": "WARNING",
      "category": "Date Format",
      "description": "Inconsistent date formats in Experience section"
    }},
    {{
      "severity": "INFO",
      "category": "Bullet Style",
      "description": "Mix of bullet styles (- and *)"
    }}
  ],
  "recommendations": [
    "Standardize date format to 'Mon YYYY - Mon YYYY'",
    "Use consistent bullet style throughout"
  ],
  "summary": "Overall formatting is good with minor inconsistencies"
}}

Categories should be: Markdown, Date Format, Bullet Style, Section Structure, Spacing, Typography
Severity levels: CRITICAL, WARNING, INFO
is_valid should be true if validation_score >= 80 and no CRITICAL issues

CRITICAL:
- Return ONLY valid JSON, no markdown formatting, no ```json code blocks
- validation_score must be 1-100
- Focus ONLY on formatting issues, not content"""

        try:
            # Try to use structured output if client supports it
            response_format = self._get_response_format(ValidationSchema)

            # Check if client supports response_format parameter
            sig = inspect.signature(self.client.generate_with_system_prompt)
            supports_response_format = 'response_format' in sig.parameters

            # Detect reasoning models - disable structured output for them
            model_name = getattr(self.client, 'model_name', '').lower()
            is_reasoning_model = any(x in model_name for x in ['r1', 'o1', 'reasoning'])

            if is_reasoning_model:
                print(f"[INFO AGENT4] Detected reasoning model ({model_name})")
                print(f"[INFO AGENT4] Disabling structured output to allow reasoning")
                supports_response_format = False

            if supports_response_format and response_format:
                print(f"[DEBUG AGENT4] Using structured output mode")
                response = self.client.generate_with_system_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.4,
                    response_format=response_format
                )
            else:
                print(f"[DEBUG AGENT4] Using traditional prompt mode")
                response = self.client.generate_with_system_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.4
                )

            return self._parse_response(response)

        except Exception as e:
            raise Exception(f"Validation failed: {str(e)}")

    def _parse_response(self, response: str) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response (expected as JSON)

        Returns:
            Structured dictionary with validation results
        """
        import json
        import re

        # Clean up response - remove markdown code blocks if present
        cleaned_response = response.strip()

        # Remove ```json and ``` markers if present
        if cleaned_response.startswith("```"):
            first_newline = cleaned_response.find('\n')
            if first_newline != -1:
                cleaned_response = cleaned_response[first_newline + 1:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3].strip()

        print(f"[DEBUG AGENT4] Cleaned response first 500 chars:\n{cleaned_response[:500]}\n")

        try:
            # Parse JSON
            parsed = json.loads(cleaned_response)

            validation_score = parsed.get("validation_score", 80)
            is_valid = parsed.get("is_valid", True)
            issues = parsed.get("issues", [])
            recommendations = parsed.get("recommendations", [])
            summary = parsed.get("summary", "Validation completed.")

            print(f"[DEBUG AGENT4] JSON parsed successfully: score={validation_score}, issues={len(issues)}")

            # Ensure score is valid
            if validation_score < 1 or validation_score > 100:
                validation_score = 80

            # Check for critical issues (override is_valid if needed)
            has_critical = any(issue.get("severity") == "CRITICAL" for issue in issues)
            if has_critical or validation_score < 80:
                is_valid = False

            return {
                "validation_score": validation_score,
                "is_valid": is_valid,
                "issues": issues,
                "recommendations": recommendations,
                "summary": summary,
                "critical_count": sum(1 for i in issues if i.get("severity") == "CRITICAL"),
                "warning_count": sum(1 for i in issues if i.get("severity") == "WARNING"),
                "info_count": sum(1 for i in issues if i.get("severity") == "INFO")
            }

        except json.JSONDecodeError as e:
            print(f"[DEBUG AGENT4] JSON parse failed: {str(e)}")
            print(f"[DEBUG AGENT4] Attempting fallback parsing...")

            # Fallback: Try to extract JSON from text
            json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    validation_score = parsed.get("validation_score", 80)
                    is_valid = parsed.get("is_valid", True)
                    issues = parsed.get("issues", [])
                    recommendations = parsed.get("recommendations", [])
                    summary = parsed.get("summary", "Validation completed.")

                    print(f"[DEBUG AGENT4] Fallback successful: score={validation_score}")

                    if validation_score < 1 or validation_score > 100:
                        validation_score = 80

                    has_critical = any(issue.get("severity") == "CRITICAL" for issue in issues)
                    if has_critical or validation_score < 80:
                        is_valid = False

                    return {
                        "validation_score": validation_score,
                        "is_valid": is_valid,
                        "issues": issues,
                        "recommendations": recommendations,
                        "summary": summary,
                        "critical_count": sum(1 for i in issues if i.get("severity") == "CRITICAL"),
                        "warning_count": sum(1 for i in issues if i.get("severity") == "WARNING"),
                        "info_count": sum(1 for i in issues if i.get("severity") == "INFO")
                    }
                except json.JSONDecodeError:
                    pass

            # If all parsing fails, return minimal result
            print(f"[DEBUG AGENT4] All parsing methods failed")

            return {
                "validation_score": 50,
                "is_valid": False,
                "issues": [{"severity": "CRITICAL", "category": "Parsing", "description": "Failed to parse validation response"}],
                "recommendations": ["Please try validation again"],
                "summary": "Validation parsing failed.",
                "critical_count": 1,
                "warning_count": 0,
                "info_count": 0
            }
