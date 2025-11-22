"""Abstract LLM client interface with multiple provider implementations."""
from abc import ABC, abstractmethod
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using system and user prompts.

        Args:
            system_prompt: System instruction
            user_prompt: User's prompt
            temperature: Sampling temperature

        Returns:
            Generated text response
        """
        pass


class GeminiClient(LLMClient):
    """Google Gemini API client."""

    def __init__(self, model_name: Optional[str] = None):
        """Initialize Gemini client."""
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.model = genai.GenerativeModel(self.model_name)

    def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """Generate using Gemini API."""
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = self.model.generate_content(
            combined_prompt,
            generation_config={
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )

        return response.text


class ClaudeClient(LLMClient):
    """Anthropic Claude API client."""

    def __init__(self, model_name: Optional[str] = None):
        """Initialize Claude client."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name or os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """Generate using Claude API."""
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=8192,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text


class CustomLLMClient(LLMClient):
    """Custom LLM API client (OpenAI-compatible)."""

    def __init__(self, model_name: Optional[str] = None):
        """Initialize custom LLM client."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        api_key = os.getenv("CUSTOM_LLM_API_KEY")
        base_url = os.getenv("CUSTOM_LLM_BASE_URL")

        if not api_key:
            raise ValueError("CUSTOM_LLM_API_KEY not found in environment variables")
        if not base_url:
            raise ValueError("CUSTOM_LLM_BASE_URL not found in environment variables")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model_name = model_name or os.getenv("CUSTOM_LLM_MODEL", "default-model")

    def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """Generate using custom LLM API."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=8192
        )

        return response.choices[0].message.content


def get_llm_client(provider: str = "gemini", model_name: Optional[str] = None) -> LLMClient:
    """
    Factory function to get appropriate LLM client.

    Args:
        provider: LLM provider name ('gemini', 'claude', 'custom')
        model_name: Optional specific model name

    Returns:
        LLMClient instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider.lower()

    if provider == "gemini":
        return GeminiClient(model_name)
    elif provider == "claude":
        return ClaudeClient(model_name)
    elif provider == "custom":
        return CustomLLMClient(model_name)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_available_models() -> dict:
    """
    Get available models from environment variables or defaults.

    Users can specify multiple models per provider using comma-separated lists:
    GEMINI_MODELS=gemini-2.0-flash-exp,gemini-1.5-pro,gemini-1.5-flash
    CLAUDE_MODELS=claude-3-5-sonnet-20241022,claude-3-5-haiku-20241022
    CUSTOM_MODELS=llama3:70b,mixtral:8x7b,gpt-4

    Returns:
        Dictionary mapping provider names to list of available models
    """
    # Default models
    default_models = {
        "gemini": [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ],
        "claude": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229"
        ],
        "custom": [
            "custom-model"
        ]
    }

    # Load from environment variables if available
    available_models = {}

    # Gemini models
    gemini_models_env = os.getenv("GEMINI_MODELS", "")
    if gemini_models_env:
        available_models["gemini"] = [m.strip() for m in gemini_models_env.split(",") if m.strip()]
    else:
        available_models["gemini"] = default_models["gemini"]

    # Claude models
    claude_models_env = os.getenv("CLAUDE_MODELS", "")
    if claude_models_env:
        available_models["claude"] = [m.strip() for m in claude_models_env.split(",") if m.strip()]
    else:
        available_models["claude"] = default_models["claude"]

    # Custom models
    custom_models_env = os.getenv("CUSTOM_MODELS", "")
    if custom_models_env:
        available_models["custom"] = [m.strip() for m in custom_models_env.split(",") if m.strip()]
    else:
        # For custom, try to get from CUSTOM_LLM_MODEL if CUSTOM_MODELS not set
        custom_model = os.getenv("CUSTOM_LLM_MODEL")
        if custom_model:
            available_models["custom"] = [custom_model]
        else:
            available_models["custom"] = default_models["custom"]

    return available_models


# Cache the available models (call get_available_models() to get fresh list)
AVAILABLE_MODELS = get_available_models()
