"""Gemini API client wrapper."""
import os
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

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
            return response.text
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
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        return self.generate_content(combined_prompt, temperature)
