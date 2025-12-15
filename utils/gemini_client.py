"""Gemini API client wrapper."""
import os
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# VERSION: 2.0 - Added JSON extraction for reasoning models
load_dotenv()


class GeminiClient:
    """Wrapper for Google Gemini API interactions."""

    def __init__(self):
        """Initialize the Gemini client with API key."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-exp")
        self.model = genai.GenerativeModel(model_name)

    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate content using Gemini API.

        Args:
            prompt: The input prompt
            temperature: Creativity level (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        generation_config = {
            "temperature": temperature,
        }

        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            content = response.text

            # Extract JSON from reasoning output if needed (for reasoning models)
            content = self._extract_response_from_reasoning_output(content)

            return content
        except Exception as e:
            raise Exception(f"Error generating content: {str(e)}")

    def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate content with a system prompt and user prompt.

        Args:
            system_prompt: System instructions for the model
            user_prompt: User input
            temperature: Creativity level

        Returns:
            Generated text response
        """
        print(f"[DEBUG GeminiClient] generate_with_system_prompt called")
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        content = self.generate_content(combined_prompt, temperature)
        print(f"[DEBUG GeminiClient] generate_content returned {len(content)} chars")

        # Extract JSON from reasoning output if needed (for reasoning models)
        content = self._extract_response_from_reasoning_output(content)

        return content

    def _extract_response_from_reasoning_output(self, content: str) -> str:
        """
        Extract actual response from reasoning model output.

        Handles various reasoning model formats:
        - DeepSeek R1: <think>...</think> tags
        - Other reasoning models: May have thinking followed by structured output

        Args:
            content: Raw model output

        Returns:
            Cleaned response with thinking removed
        """
        import re

        print(f"[DEBUG EXTRACTION] Starting extraction, content length: {len(content)} chars")
        print(f"[DEBUG EXTRACTION] Content starts with: {content[:100]}")

        # Method 1: Handle explicit thinking tags (DeepSeek R1, etc.)
        if "<think>" in content and "</think>" in content:
            # Extract everything after the last closing </think> tag
            parts = content.split("</think>")
            if len(parts) > 1:
                extracted = parts[-1].strip()
                print(f"[DEBUG] Stripped <think> tags, response length: {len(extracted)} chars")
                return extracted

        # Method 2: Try to extract JSON from mixed content
        # If response starts with non-JSON text but contains JSON, extract it
        content_stripped = content.strip()

        # Check if response starts with JSON
        if content_stripped.startswith('{') or content_stripped.startswith('['):
            return content  # Already clean JSON

        # Try to find JSON object in the response - use greedy match to get complete JSON
        # Look for the first { and try to match to the last }
        json_start = content.find('{')
        if json_start != -1:
            # Find the matching closing brace
            json_end = content.rfind('}')
            if json_end != -1 and json_end > json_start:
                potential_json = content[json_start:json_end + 1]
                # Verify it looks like valid JSON structure
                if '"score"' in potential_json or '"analysis"' in potential_json or '"suggestions"' in potential_json:
                    print(f"[DEBUG] Extracted JSON from mixed content (full match), length: {len(potential_json)} chars")
                    return potential_json

        # Fallback: Try regex approach for complex cases
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            potential_json = json_match.group(0)
            # Verify it looks like valid JSON structure
            if '"score"' in potential_json or '"analysis"' in potential_json:
                print(f"[DEBUG] Extracted JSON from mixed content (regex), length: {len(potential_json)} chars")
                return potential_json

        # Method 3: No special handling needed
        print(f"[DEBUG] No JSON extraction performed")
        return content
