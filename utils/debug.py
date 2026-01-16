"""Debug utilities for capturing and displaying LLM interactions."""
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configure logging
logger = logging.getLogger("resume_customizer")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class LLMInteractionCapture:
    """Captures and stores LLM interactions for debugging."""

    def __init__(self):
        """Initialize the interaction capture."""
        self.interactions: List[Dict[str, Any]] = []
        self.enabled = False

    def enable(self):
        """Enable interaction capture."""
        self.enabled = True
        logger.setLevel(logging.DEBUG)

    def disable(self):
        """Disable interaction capture."""
        self.enabled = False
        logger.setLevel(logging.INFO)

    def capture_llm_call(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response: str,
        temperature: float = 0.7,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Capture a complete LLM interaction.

        Args:
            provider: LLM provider (gemini, claude, custom)
            model: Model name used
            system_prompt: System prompt sent
            user_prompt: User prompt sent
            response: LLM response received
            temperature: Temperature parameter used
            duration_ms: Duration in milliseconds
            error: Error message if call failed
        """
        if not self.enabled:
            return

        interaction = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response": response,
            "temperature": temperature,
            "duration_ms": duration_ms,
            "error": error,
            "combined_prompt_length": len(system_prompt) + len(user_prompt),
            "response_length": len(response) if response else 0,
        }

        self.interactions.append(interaction)

        # Log to console
        logger.debug(f"\n{'='*80}")
        logger.debug(f"LLM CALL: {provider.upper()} ({model})")
        logger.debug(f"{'='*80}")
        logger.debug(f"SYSTEM PROMPT:\n{system_prompt[:200]}...")
        logger.debug(f"\nUSER PROMPT:\n{user_prompt[:200]}...")
        logger.debug(f"\nRESPONSE:\n{response[:200] if response else 'ERROR'}...")
        if error:
            logger.error(f"ERROR: {error}")
        if duration_ms:
            logger.debug(f"Duration: {duration_ms:.2f}ms")
        logger.debug(f"{'='*80}\n")

    def get_last_interaction(self) -> Optional[Dict[str, Any]]:
        """Get the last captured interaction."""
        return self.interactions[-1] if self.interactions else None

    def get_all_interactions(self) -> List[Dict[str, Any]]:
        """Get all captured interactions."""
        return self.interactions

    def clear(self):
        """Clear all captured interactions."""
        self.interactions = []

    def format_for_display(self, interaction: Dict[str, Any], max_length: int = 500) -> Dict[str, str]:
        """
        Format an interaction for display in Streamlit.

        Args:
            interaction: The interaction dict to format
            max_length: Maximum length to show for prompts/responses

        Returns:
            Dict with formatted strings for display
        """
        return {
            "timestamp": interaction.get("timestamp", "N/A"),
            "provider": interaction.get("provider", "N/A").upper(),
            "model": interaction.get("model", "N/A"),
            "temperature": f"{interaction.get('temperature', 0.7):.2f}",
            "duration": f"{interaction.get('duration_ms', 0):.0f}ms" if interaction.get('duration_ms') else "N/A",
            "system_prompt": interaction.get("system_prompt", "")[:max_length],
            "user_prompt": interaction.get("user_prompt", "")[:max_length],
            "response": interaction.get("response", "")[:max_length],
            "error": interaction.get("error"),
            "prompt_chars": interaction.get("combined_prompt_length", 0),
            "response_chars": interaction.get("response_length", 0),
        }


# Global instance
_capture = LLMInteractionCapture()


def enable_debug():
    """Enable debug mode globally."""
    _capture.enable()


def disable_debug():
    """Disable debug mode globally."""
    _capture.disable()


def capture_llm_call(
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    response: str,
    temperature: float = 0.7,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None
):
    """Capture an LLM interaction."""
    _capture.capture_llm_call(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response=response,
        temperature=temperature,
        duration_ms=duration_ms,
        error=error,
    )


def get_last_interaction() -> Optional[Dict[str, Any]]:
    """Get the last LLM interaction."""
    return _capture.get_last_interaction()


def get_all_interactions() -> List[Dict[str, Any]]:
    """Get all LLM interactions."""
    return _capture.get_all_interactions()


def clear_interactions():
    """Clear all interactions."""
    _capture.clear()


def format_interaction(interaction: Dict[str, Any], max_length: int = 500) -> Dict[str, str]:
    """Format an interaction for display."""
    return _capture.format_for_display(interaction, max_length)


def get_capture_instance() -> LLMInteractionCapture:
    """Get the global capture instance."""
    return _capture
