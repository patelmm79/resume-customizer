"""Agent 1: Resume Scorer and Analyzer."""
from typing import Dict, List
from utils.agent_helper import get_agent_llm_client
import re


class ResumeScorerAgent:
    """Agent that scores resumes and suggests improvements."""

    def __init__(self):
        """Initialize the scorer agent."""
        self.client = get_agent_llm_client()
        self.max_job_description_chars = 30000  # ~7500 tokens (4 chars per token average)

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

Please format your response EXACTLY as follows:

SCORE: [number from 1-100]

ANALYSIS:
[Your detailed analysis here]

SUGGESTIONS:
- [CATEGORY: Skills] Add skill: Python
- [CATEGORY: Skills] Add skill: Docker
- [CATEGORY: Skills] Add skill: Kubernetes
- [CATEGORY: Summary] [DESCRIPTION: Emphasize cloud architecture and leadership experience] [SUGGESTED_TEXT: Results-driven Data Scientist with 8+ years of experience building ML pipelines and deploying models at scale. Proven track record of reducing infrastructure costs by 40% through optimization and driving data-driven decision making across cross-functional teams.]
- [CATEGORY: Experience] [DESCRIPTION: Quantify achievement in recent engineering role] [SUGGESTED_TEXT: Led a team of 5 engineers to architect and deploy a real-time fraud detection system processing 10M+ transactions daily, reducing false positives by 35% and saving $2M annually.]
(Continue with more suggestions as needed)

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
- Use this format: [DESCRIPTION: Brief justification] [SUGGESTED_TEXT: Actual text to use]
- DESCRIPTION: A brief phrase explaining why this change is suggested (shown in checkbox)
- SUGGESTED_TEXT: The COMPLETE actual text to insert/replace (shown in text box)
- For Summary: Provide a complete paragraph rewrite based ONLY on facts from the resume
- For Experience: Provide a complete bullet point based ONLY on existing information
- NEVER INVENT metrics, numbers, team sizes, percentages, or timeframes not in the original resume
- Use placeholders like "[X%]", "[number of team members]", "[timeframe]" when suggesting quantification
- Do NOT write vague instructions - always provide concrete, ready-to-use text
- Users will be able to edit the SUGGESTED_TEXT before applying it

CRITICAL REMINDER: Do NOT fabricate any specific numbers or facts. Only rephrase what's already in the resume, or use placeholders for missing metrics.

Skills not checked will NOT be added to the resume"""

        try:
            response = self.client.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )

            print(f"[DEBUG] Raw LLM response length: {len(response)} chars")
            print(f"[DEBUG] Response preview: {response[:500]}...")

            result = self._parse_response(response)
            print(f"[DEBUG] Parsed - Score: {result['score']}, Analysis length: {len(result['analysis'])}, Suggestions: {len(result['suggestions'])}")

            return result

        except Exception as e:
            raise Exception(f"Error in resume analysis: {str(e)}")

    def _extract_suggestions_from_text(self, text: str) -> list:
        """Extract suggestions from unstructured text."""
        suggestions = []
        # Look for bulleted lists or numbered lists
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or re.match(r'^\d+\.', line):
                # This looks like a suggestion
                suggestion_text = re.sub(r'^[-•\d.]\s*', '', line).strip()
                if len(suggestion_text) > 10:  # Filter out very short lines
                    suggestions.append({
                        "id": len(suggestions),
                        "text": suggestion_text,
                        "category": "General",
                        "selected": True,
                        "edited_text": suggestion_text
                    })
        return suggestions

    def _parse_response(self, response: str) -> Dict:
        """
        Parse the LLM response into structured data.

        Args:
            response: Raw LLM response

        Returns:
            Structured dictionary with score, analysis, and suggestions
        """
        score = None
        analysis = []
        suggestions = []

        # Check if response follows the expected format
        if "SCORE:" in response and "SUGGESTIONS:" in response:
            # Structured format parsing
            lines = response.strip().split('\n')
            current_section = None

            for line in lines:
                line = line.strip()

                if line.startswith("SCORE:"):
                    score_text = line.replace("SCORE:", "").strip()
                    try:
                        score = int(score_text)
                    except ValueError:
                        match = re.search(r'\d+', score_text)
                        if match:
                            score = int(match.group())
                    current_section = "score"

                elif line.startswith("ANALYSIS:"):
                    current_section = "analysis"
                    analysis_text = line.replace("ANALYSIS:", "").strip()
                    if analysis_text:
                        analysis.append(analysis_text)

                elif line.startswith("SUGGESTIONS:"):
                    current_section = "suggestions"

                elif line and current_section == "analysis":
                    analysis.append(line)

                elif line and current_section == "suggestions" and line.startswith("-"):
                    # Parse structured suggestion
                    suggestion_text = line[1:].strip()
                    category = "General"

                    if suggestion_text.startswith("[CATEGORY:"):
                        end_bracket = suggestion_text.find("]")
                        if end_bracket != -1:
                            category = suggestion_text[10:end_bracket].strip()
                            suggestion_text = suggestion_text[end_bracket + 1:].strip()

                    description = None
                    suggested_text = None

                    if "[DESCRIPTION:" in suggestion_text:
                        desc_start = suggestion_text.find("[DESCRIPTION:") + 13
                        desc_end = suggestion_text.find("]", desc_start)
                        if desc_end != -1:
                            description = suggestion_text[desc_start:desc_end].strip()
                            suggestion_text = suggestion_text[desc_end + 1:].strip()

                    if "[SUGGESTED_TEXT:" in suggestion_text:
                        text_start = suggestion_text.find("[SUGGESTED_TEXT:") + 16
                        text_end = suggestion_text.find("]", text_start)
                        if text_end != -1:
                            suggested_text = suggestion_text[text_start:text_end].strip()

                    display_text = description if description and suggested_text else suggestion_text
                    edited_text = suggested_text if suggested_text else suggestion_text

                    suggestions.append({
                        "id": len(suggestions),
                        "text": display_text,
                        "category": category,
                        "selected": True,
                        "edited_text": edited_text
                    })
        else:
            # Fallback: conversational format
            print("[DEBUG] Response not in expected format, using fallback parsing")

            # Extract score
            score_match = re.search(r'(?:score|rating).*?(\d+)(?:/100|\s+out of 100)', response, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
            else:
                numbers = re.findall(r'\b(\d+)\b', response)
                for num in numbers:
                    n = int(num)
                    if 1 <= n <= 100:
                        score = n
                        break

            # Use entire response as analysis
            analysis = [response]

            # Extract suggestions
            suggestions = self._extract_suggestions_from_text(response)

        # Ensure score is valid
        if score is None or score < 1 or score > 100:
            score = 50

        return {
            "score": score,
            "analysis": "\n".join(analysis) if analysis else "Analysis not available",
            "suggestions": suggestions
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
