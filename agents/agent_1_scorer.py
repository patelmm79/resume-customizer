"""Agent 1: Resume Scorer and Analyzer - VERSION 3.0 with structured output."""
from typing import Dict, List, Optional
from utils.agent_helper import get_agent_llm_client
from agents.schemas import ResumeAnalysisSchema, ResumeScoreSchema
import re

print("[MODULE LOAD] agent_1_scorer.py loaded - VERSION 3.0 with structured output")


class ResumeScorerAgent:
    """Agent that scores resumes and suggests improvements."""

    def __init__(self):
        """Initialize the scorer agent."""
        self.client = get_agent_llm_client()
        print(f"[DEBUG AGENT1] Client type: {type(self.client).__name__}")
        print(f"[DEBUG AGENT1] Client module: {type(self.client).__module__}")
        print(f"[DEBUG AGENT1] Has extraction method: {hasattr(self.client, '_extract_response_from_reasoning_output')}")
        print(f"[DEBUG AGENT1] Supports response_format: {hasattr(self.client, 'generate_with_system_prompt') and 'response_format' in self.client.generate_with_system_prompt.__code__.co_varnames}")
        self.max_job_description_chars = 30000  # ~7500 tokens (4 chars per token average)

    def _get_response_format(self, schema_class) -> Optional[Dict]:
        """
        Build response_format parameter for structured output.

        Args:
            schema_class: Pydantic model class (e.g., ResumeAnalysisSchema)

        Returns:
            Dictionary for response_format parameter, or None if not supported
        """
        try:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_class.__name__,
                    "schema": schema_class.model_json_schema(),
                    "strict": True,
                },
            }
            print(f"[DEBUG AGENT1] Built response_format for {schema_class.__name__}")
            return response_format
        except Exception as e:
            print(f"[DEBUG AGENT1] Could not build response_format: {e}")
            return None

    def _truncate_job_description(self, job_description: str) -> str:
        """
        Intelligently truncate job description if too long.

        Args:
            job_description: Original job description

        Returns:
            Truncated job description preserving key information
        """
        if len(job_description) <= self.max_job_description_chars:
            return job_description

        print(f"[INFO] Job description is {len(job_description)} chars, truncating to {self.max_job_description_chars}")

        # Extract key sections using common patterns
        sections = {
            'responsibilities': [],
            'requirements': [],
            'qualifications': [],
            'skills': [],
            'other': []
        }

        lines = job_description.split('\n')
        current_section = 'other'

        for line in lines:
            line_lower = line.lower().strip()

            # Detect section headers
            if any(keyword in line_lower for keyword in ['responsibilities', 'duties', 'what you\'ll do']):
                current_section = 'responsibilities'
            elif any(keyword in line_lower for keyword in ['requirements', 'required', 'must have']):
                current_section = 'requirements'
            elif any(keyword in line_lower for keyword in ['qualifications', 'experience', 'background']):
                current_section = 'qualifications'
            elif any(keyword in line_lower for keyword in ['skills', 'technical', 'technologies']):
                current_section = 'skills'

            # Add line to current section
            if line.strip():
                sections[current_section].append(line)

        # Prioritize important sections and truncate
        result = []
        char_budget = self.max_job_description_chars

        # Priority order: requirements > skills > qualifications > responsibilities > other
        priority_sections = ['requirements', 'skills', 'qualifications', 'responsibilities', 'other']

        for section_name in priority_sections:
            section_content = '\n'.join(sections[section_name])
            if section_content and char_budget > 0:
                if len(section_content) <= char_budget:
                    result.append(section_content)
                    char_budget -= len(section_content)
                else:
                    # Truncate this section
                    result.append(section_content[:char_budget] + "\n[... truncated ...]")
                    char_budget = 0
                    break

        truncated = '\n'.join(result)
        print(f"[INFO] Truncated job description to {len(truncated)} chars")
        return truncated

    def analyze_and_score(
        self,
        resume_content: str,
        job_description: str
    ) -> Dict:
        """
        Analyze resume against job description and provide score with suggestions.

        Args:
            resume_content: The resume in markdown format
            job_description: The job description text

        Returns:
            Dictionary containing:
                - score: int (1-100)
                - analysis: str
                - suggestions: List[Dict] with 'id', 'text', and 'category'
        """
        # Truncate job description if too long
        job_description = self._truncate_job_description(job_description)

        system_prompt = """You are an expert resume analyzer and career coach. Your job is to:
1. Carefully compare a resume against a job description
2. Provide a compatibility score from 1-100 (where 100 is perfect match)
3. Identify specific, actionable improvements

Focus on:
- Keyword matching and ATS optimization
- Relevant skills and experience alignment
- Quantifiable achievements
- Professional summary optimization
- Removing irrelevant information
- Highlighting transferable skills

CRITICAL - NEVER FABRICATE OR HALLUCINATE:
- NEVER invent specific numbers, metrics, or facts not present in the original resume
- NEVER add team sizes, percentages, dollar amounts, or timeframes that aren't already stated
- If suggesting quantifiable achievements, use placeholders like "[X%]" or "[number]" that the user must fill in
- ONLY rephrase, reframe, or reorganize information that already exists in the resume
- When in doubt, suggest the addition without inventing specific details

IMPORTANT for Skills:
- Create a SEPARATE checklist item for EACH individual skill from the job description
- ONLY suggest skills that are NOT already present in the resume (check the Skills section carefully)
- Do NOT suggest skills that already appear in the resume, even with slightly different wording
- Each skill should be its own suggestion so the user can selectively approve which skills to add
- Only skills that are checked will be added to the resume

IMPORTANT for Summary and Experience suggestions:
- For Summary: Provide the ACTUAL suggested summary text, not just a description of what to change
- For Experience: Provide the ACTUAL suggested bullet point or text, not just instructions
- NEVER invent specific metrics - use placeholders like "[X%]", "[number]", "[timeframe]" for the user to fill in
- Users will be able to edit this text before applying it
- Make suggestions specific and ready-to-use, but truthful

Be specific and actionable in your suggestions, but NEVER fabricate facts."""

        user_prompt = f"""Please analyze this resume against the job description and provide:

1. A score from 1-100 for how well this resume matches the job
2. A brief analysis explaining the score
3. A list of specific, actionable suggestions for improvement

RESUME:
{resume_content}

JOB DESCRIPTION:
{job_description}

CRITICAL FORMAT REQUIREMENTS:

For Skills:
- BEFORE suggesting a skill, carefully check if it already exists in the resume's Skills section
- Do NOT suggest skills that are already listed (e.g., if "Tableau" is in the resume, don't suggest adding it)
- Do NOT suggest skills with slightly different wording (e.g., if "Stakeholder Management" is listed, don't suggest "Stakeholder Engagement")
- Only suggest skills that are genuinely missing but relevant to the job description
- For skills, create ONE suggestion per skill
- Each skill should be its own line item so the user can individually approve which skills to add
- Format: "Add skill: [Skill Name]"

For Summary and Experience:
- DESCRIPTION: A brief phrase explaining why this change is suggested (shown in checkbox)
- SUGGESTED_TEXT: The COMPLETE actual text to insert/replace (shown in text box)
- For Summary: Provide a complete paragraph rewrite based ONLY on facts from the resume
- For Experience: Provide a complete bullet point based ONLY on existing information
- NEVER INVENT metrics, numbers, team sizes, percentages, or timeframes not in the original resume
- Use placeholders like "[X%]", "[number of team members]", "[timeframe]" when suggesting quantification
- Do NOT write vague instructions - always provide concrete, ready-to-use text
- Users will be able to edit the SUGGESTED_TEXT before applying it

CRITICAL REMINDER: Do NOT fabricate any specific numbers or facts. Only rephrase what's already in the resume, or use placeholders for missing metrics.

Please provide your response in VALID JSON format ONLY (no markdown, no code blocks, just pure JSON):

{{
  "score": 72,
  "analysis": "Your detailed analysis explaining the score, what matches well, and what could be improved.",
  "suggestions": [
    {{
      "category": "Skills",
      "text": "Add skill: Python",
      "suggested_text": "Add skill: Python"
    }},
    {{
      "category": "Skills",
      "text": "Add skill: Docker",
      "suggested_text": "Add skill: Docker"
    }},
    {{
      "category": "Summary",
      "text": "Emphasize cloud architecture and leadership experience",
      "suggested_text": "Results-driven Data Scientist with 8+ years of experience building ML pipelines and deploying models at scale. Proven track record of reducing infrastructure costs by [X%] through optimization."
    }},
    {{
      "category": "Experience",
      "text": "Quantify achievement in recent engineering role",
      "suggested_text": "Led a team of [number] engineers to architect and deploy a real-time fraud detection system processing [volume] transactions daily."
    }}
  ]
}}

CRITICAL:
- Return ONLY valid JSON, no markdown formatting, no ```json code blocks
- Each suggestion must have category, text, and suggested_text fields
- Use placeholders like [X%], [number], [timeframe] for metrics not in the original resume
- Skills not checked by user will NOT be added to the resume"""

        try:
            # Try to use structured output if client supports it
            response_format = self._get_response_format(ResumeAnalysisSchema)

            # Check if client supports response_format parameter
            import inspect
            sig = inspect.signature(self.client.generate_with_system_prompt)
            supports_response_format = 'response_format' in sig.parameters

            # IMPORTANT: Disable structured output for reasoning models
            # Reasoning models (R1, o1) need to think freely before formatting
            # Structured output prevents their deep reasoning capability
            model_name = getattr(self.client, 'model_name', '').lower()
            is_reasoning_model = any(x in model_name for x in ['r1', 'o1', 'reasoning'])

            if is_reasoning_model:
                print(f"[INFO AGENT1] Detected reasoning model ({model_name})")
                print(f"[INFO AGENT1] Disabling structured output to allow reasoning")
                print(f"[INFO AGENT1] Using controlled reasoning budget (45-60 second target)")
                supports_response_format = False  # Force traditional mode

            if supports_response_format and response_format:
                print(f"[DEBUG AGENT1] Using structured output mode")
                response = self.client.generate_with_system_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.7,
                    response_format=response_format
                )
            else:
                print(f"[DEBUG AGENT1] Using traditional prompt mode")
                # Let client auto-calculate max_tokens based on available context
                # This prevents truncation with large inputs
                print(f"[DEBUG AGENT1] Using auto-calculated max_tokens (based on input size)")
                response = self.client.generate_with_system_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.7,
                    max_tokens=None  # Auto-calculate based on available context
                )

            print(f"[DEBUG] Raw LLM response length: {len(response)} chars")
            print(f"[DEBUG] Response preview: {response[:500]}...")

            result = self._parse_response(response)
            print(f"[DEBUG] Parsed - Score: {result['score']}, Analysis length: {len(result['analysis'])}, Suggestions: {len(result['suggestions'])}")

            return result

        except Exception as e:
            raise Exception(f"Error in resume analysis: {str(e)}")

    def _parse_response(self, response: str) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response (expected as JSON)

        Returns:
            Structured dictionary with score, analysis, and suggestions
        """
        import json

        # Clean up response - remove markdown code blocks if present
        cleaned_response = response.strip()

        # Remove ```json and ``` markers if present
        if cleaned_response.startswith("```"):
            first_newline = cleaned_response.find('\n')
            if first_newline != -1:
                cleaned_response = cleaned_response[first_newline + 1:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3].strip()

        print(f"[DEBUG] Cleaned response first 500 chars:\n{cleaned_response[:500]}\n")

        try:
            # Parse JSON
            parsed = json.loads(cleaned_response)

            score = parsed.get("score", 50)
            analysis = parsed.get("analysis", "Analysis not available")
            raw_suggestions = parsed.get("suggestions", [])

            # Convert to internal format
            suggestions = []
            for idx, suggestion in enumerate(raw_suggestions):
                suggestions.append({
                    "id": idx,
                    "text": suggestion.get("text", ""),
                    "category": suggestion.get("category", "General"),
                    "selected": True,
                    "edited_text": suggestion.get("suggested_text", suggestion.get("text", ""))
                })

            print(f"[DEBUG] JSON parsed successfully: {len(suggestions)} suggestions")

            # Ensure score is valid
            if score is None or score < 1 or score > 100:
                score = 50

            return {
                "score": score,
                "analysis": analysis,
                "suggestions": suggestions
            }

        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON parse failed: {str(e)}")
            print(f"[DEBUG] Attempting fallback parsing...")

            # Fallback: Try to extract JSON from text
            json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    score = parsed.get("score", 50)
                    analysis = parsed.get("analysis", "Analysis not available")
                    raw_suggestions = parsed.get("suggestions", [])

                    suggestions = []
                    for idx, suggestion in enumerate(raw_suggestions):
                        suggestions.append({
                            "id": idx,
                            "text": suggestion.get("text", ""),
                            "category": suggestion.get("category", "General"),
                            "selected": True,
                            "edited_text": suggestion.get("suggested_text", suggestion.get("text", ""))
                        })

                    print(f"[DEBUG] Fallback successful: {len(suggestions)} suggestions")

                    if score is None or score < 1 or score > 100:
                        score = 50

                    return {
                        "score": score,
                        "analysis": analysis,
                        "suggestions": suggestions
                    }
                except json.JSONDecodeError:
                    pass

            # If all parsing fails, return minimal result
            print(f"[DEBUG] All parsing methods failed")

            return {
                "score": 50,
                "analysis": "Failed to parse response. Please try again.",
                "suggestions": []
            }

    def score_only(
        self,
        resume_content: str,
        job_description: str
    ) -> Dict:
        """
        Score resume against job description without generating suggestions.
        Used for rescoring and final scoring.

        Args:
            resume_content: The resume in markdown format
            job_description: The job description text

        Returns:
            Dictionary containing:
                - score: int (1-100)
                - analysis: str (brief evaluation)
        """
        # Truncate job description if too long
        job_description = self._truncate_job_description(job_description)

        system_prompt = """You are an expert resume analyzer. Your job is to:
1. Carefully compare a resume against a job description
2. Provide a compatibility score from 1-100 (where 100 is perfect match)
3. Provide brief analysis of the match quality

Focus on:
- Keyword matching and ATS optimization
- Relevant skills and experience alignment
- Overall suitability for the role"""

        user_prompt = f"""Please score this resume against the job description:

RESUME:
{resume_content}

JOB DESCRIPTION:
{job_description}

Please format your response EXACTLY as follows:

SCORE: [number from 1-100]

ANALYSIS:
[Your brief analysis of the match quality and key strengths]"""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )

            # Parse just score and analysis
            lines = response.strip().split('\n')
            score = None
            analysis = []
            current_section = None

            for line in lines:
                line = line.strip()

                if line.startswith("SCORE:"):
                    score_text = line.replace("SCORE:", "").strip()
                    try:
                        score = int(score_text)
                    except ValueError:
                        import re
                        match = re.search(r'\d+', score_text)
                        if match:
                            score = int(match.group())
                        else:
                            score = 50
                    current_section = "score"

                elif line.startswith("ANALYSIS:"):
                    current_section = "analysis"

                elif line and current_section == "analysis":
                    analysis.append(line)

            if score is None or score < 1 or score > 100:
                score = 50

            return {
                "score": score,
                "analysis": "\n".join(analysis)
            }

        except Exception as e:
            raise Exception(f"Error in resume scoring: {str(e)}")
