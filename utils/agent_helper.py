"""Helper functions for agents to access LLM clients."""
import streamlit as st
from utils.llm_client import get_llm_client, LLMClient
from utils.gemini_client import GeminiClient


def get_agent_llm_client() -> LLMClient:
    """
    Get the appropriate LLM client based on user's selection in Streamlit.
    Falls back to Gemini if not in Streamlit context.

    Returns:
        LLMClient instance configured for the selected provider/model
    """
    try:
        # Try to get from Streamlit session state
        if hasattr(st, 'session_state'):
            provider = getattr(st.session_state, 'selected_provider', 'gemini')
            model = getattr(st.session_state, 'selected_model', None)
            return get_llm_client(provider, model)
    except:
        pass

    # Fallback to Gemini client for backward compatibility
    return GeminiClient()
