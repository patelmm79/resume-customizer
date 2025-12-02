"""Helper functions for agents to access LLM clients."""
import streamlit as st
from utils.llm_client import get_llm_client, LLMClient
from utils.gemini_client import GeminiClient
import sys


def get_agent_llm_client() -> LLMClient:
    """
    Get the appropriate LLM client based on user's selection in Streamlit.
    Falls back to Gemini if not in Streamlit context.

    Returns:
        LLMClient instance configured for the selected provider/model
    """
    provider = None
    model = None

    try:
        # Try to get from Streamlit session state
        # Check multiple ways to access session state
        if hasattr(st, 'session_state'):
            print(f"[DEBUG] st.session_state exists: {st.session_state is not None}")

            # Method 1: Direct attribute access
            if hasattr(st.session_state, 'selected_provider'):
                provider = st.session_state.selected_provider
                model = getattr(st.session_state, 'selected_model', None)
                print(f"[DEBUG] Found provider in session state: {provider}, model: {model}")

            # Method 2: Dictionary-style access (fallback)
            elif isinstance(st.session_state, dict) and 'selected_provider' in st.session_state:
                provider = st.session_state['selected_provider']
                model = st.session_state.get('selected_model', None)
                print(f"[DEBUG] Found provider via dict access: {provider}, model: {model}")
            else:
                print(f"[DEBUG] Session state exists but no provider found. Keys: {list(st.session_state.keys()) if hasattr(st.session_state, 'keys') else 'N/A'}")
        else:
            print("[DEBUG] st.session_state does not exist")

        # If we found a provider, use it
        if provider:
            print(f"[DEBUG] Creating LLM client with provider={provider}, model={model}")
            return get_llm_client(provider, model)

    except Exception as e:
        print(f"[DEBUG] Exception getting session state: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)

    # Fallback to Gemini client for backward compatibility
    print("[DEBUG] WARNING: Using fallback Gemini client (no provider in session state)")
    return GeminiClient()
