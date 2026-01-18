"""Unified tracing wrapper for LangSmith and Langfuse."""
import os
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Global clients
_langfuse_client = None
_langsmith_enabled = False


def initialize_tracing():
    """Initialize both LangSmith and Langfuse clients."""
    global _langfuse_client, _langsmith_enabled

    # Check LangSmith
    from utils.langsmith_config import is_langsmith_enabled
    _langsmith_enabled = is_langsmith_enabled()

    # Initialize Langfuse
    from utils.langfuse_config import configure_langfuse
    _langfuse_client = configure_langfuse()


def is_tracing_enabled():
    """Check if any tracing platform is enabled."""
    global _langfuse_client, _langsmith_enabled
    return _langsmith_enabled or _langfuse_client is not None


def log_llm_call(
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    response: str,
    temperature: float,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Log LLM call to both LangSmith and Langfuse.

    Args:
        provider: LLM provider (gemini, claude, custom)
        model: Model name
        system_prompt: Full system prompt
        user_prompt: Full user prompt
        response: LLM response text
        temperature: Temperature parameter used
        duration_ms: Request duration in milliseconds
        error: Error message if request failed
        metadata: Additional metadata to log
    """
    global _langfuse_client

    if not (_langsmith_enabled or _langfuse_client):
        return

    # Prepare common data
    combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
    timestamp = datetime.utcnow().isoformat()

    metadata = metadata or {}
    metadata.update({
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "system_prompt_length": len(system_prompt),
        "user_prompt_length": len(user_prompt),
        "response_length": len(response) if response else 0,
        "duration_ms": duration_ms,
    })

    # Log to Langfuse if enabled
    if _langfuse_client:
        try:
            trace_id = f"{provider}_{int(time.time() * 1000)}"

            # Langfuse SDK: Create trace through the client
            trace = _langfuse_client.trace(
                name=f"LLM Call - {provider.upper()}",
                input={"system": system_prompt, "user": user_prompt},
                metadata=metadata,
            )

            # Create generation event within the trace
            if error:
                _langfuse_client.generation(
                    trace_id=trace.id if hasattr(trace, 'id') else trace_id,
                    name=model,
                    model=model,
                    input=combined_prompt,
                    output=None,
                    level="ERROR",
                    status_message=error,
                    metadata=metadata,
                )
            else:
                _langfuse_client.generation(
                    trace_id=trace.id if hasattr(trace, 'id') else trace_id,
                    name=model,
                    model=model,
                    input=combined_prompt,
                    output=response,
                    usage={
                        "input": len(system_prompt) + len(user_prompt),
                        "output": len(response) if response else 0,
                    },
                    metadata=metadata,
                )

            # Flush to ensure traces are sent to Langfuse
            _langfuse_client.flush()

        except AttributeError as e:
            print(f"[WARNING] Langfuse API error (method not found): {e}")
            print(f"[DEBUG] Available Langfuse client methods: {[m for m in dir(_langfuse_client) if not m.startswith('_')]}")
        except Exception as e:
            print(f"[WARNING] Failed to log to Langfuse: {e}")
            import traceback
            traceback.print_exc()

    # Log to LangSmith via debug capture
    try:
        from utils.debug import capture_llm_call
        capture_llm_call(
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=response,
            temperature=temperature,
            duration_ms=duration_ms,
            error=error,
        )
    except Exception as e:
        print(f"[WARNING] Failed to log to debug capture: {e}")


def get_tracing_status():
    """Get status of both tracing platforms."""
    global _langfuse_client, _langsmith_enabled

    return {
        "langsmith_enabled": _langsmith_enabled,
        "langfuse_enabled": _langfuse_client is not None,
        "any_enabled": _langsmith_enabled or _langfuse_client is not None,
    }
