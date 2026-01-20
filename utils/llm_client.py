"""Abstract LLM client interface with multiple provider implementations."""
from abc import ABC, abstractmethod
from typing import Optional
import os
from dotenv import load_dotenv

# Import LangSmith for tracing (optional - only if available)
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    # Create a no-op decorator if langsmith is not installed
    def traceable(func=None, *, name=None, tags=None, metadata=None, run_type=None):
        """No-op decorator when langsmith is not available."""
        if func is None:
            return lambda f: f
        return func

load_dotenv()

# Initialize unified tracing (LangSmith + Langfuse)
# Note: This is imported but not initialized here - initialization happens in app.py with caching
try:
    from utils.langfuse_wrapper import initialize_tracing, log_llm_call
except Exception as e:
    print(f"[WARNING] Failed to import tracing: {e}")
    # Define stub functions if import fails
    def log_llm_call(*args, **kwargs):
        pass


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
        print(f"[DEBUG EXTRACTION] json_start position: {json_start}")

        # Also check for common markers that might indicate where JSON starts
        json_markers = [
            'json\n{', 'JSON:\n{', '```json',
            'Here is the JSON', 'Here\'s the JSON',
            'The JSON response', 'Final response:',
            '"score":', "'score':"
        ]
        for marker in json_markers:
            marker_pos = content.lower().find(marker.lower())
            if marker_pos != -1:
                print(f"[DEBUG EXTRACTION] Found marker '{marker}' at position {marker_pos}")
                # Look for { after this marker
                temp_start = content.find('{', marker_pos)
                if temp_start != -1 and (json_start == -1 or temp_start < json_start):
                    json_start = temp_start
                    print(f"[DEBUG EXTRACTION] Updated json_start to {json_start}")

        if json_start != -1:
            # Find the matching closing brace
            json_end = content.rfind('}')
            print(f"[DEBUG EXTRACTION] json_end position: {json_end}")
            if json_end != -1 and json_end > json_start:
                potential_json = content[json_start:json_end + 1]
                print(f"[DEBUG EXTRACTION] Potential JSON length: {len(potential_json)} chars")
                print("[DEBUG EXTRACTION] Contains 'score':", '"score"' in potential_json)
                print("[DEBUG EXTRACTION] Contains 'analysis':", '"analysis"' in potential_json)
                print("[DEBUG EXTRACTION] Contains 'suggestions':", '"suggestions"' in potential_json)
                # Verify it looks like valid JSON structure
                if '"score"' in potential_json or '"analysis"' in potential_json or '"suggestions"' in potential_json:
                    print(f"[DEBUG] Extracted JSON from mixed content (full match), length: {len(potential_json)} chars")
                    return potential_json
                else:
                    print(f"[DEBUG EXTRACTION] Potential JSON failed validation check")
                    print(f"[DEBUG EXTRACTION] First 500 chars: {potential_json[:500]}")

        # Fallback: Try regex approach for complex cases
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            potential_json = json_match.group(0)
            # Verify it looks like valid JSON structure
            if '"score"' in potential_json or '"analysis"' in potential_json:
                print(f"[DEBUG] Extracted JSON from mixed content (regex), length: {len(potential_json)} chars")
                return potential_json

        # Method 3: No JSON found - check if this is pure reasoning output (DeepSeek R1 issue)
        # If the content is very long and contains reasoning keywords but no JSON markers,
        # this is likely a reasoning model that ignored the JSON formatting instruction
        is_reasoning_only = (
            len(content) > 10000 and
            json_start == -1 and
            any(phrase in content.lower() for phrase in [
                'i need to analyze', 'let me go through', 'step by step',
                'first,', 'the score is', 'the user has provided'
            ])
        )

        if is_reasoning_only:
            print(f"[DEBUG EXTRACTION] Detected pure reasoning output without JSON (DeepSeek R1 issue)")
            print(f"[DEBUG EXTRACTION] Content length: {len(content)} chars, no JSON found")
            print(f"[DEBUG EXTRACTION] This model may not support structured output well")
            # Return a helpful error message instead of the raw reasoning
            return content  # Return as-is for now, but flag the issue

        print(f"[DEBUG] No JSON extraction performed")
        print(f"[DEBUG EXTRACTION] Last 500 chars of content: {content[-500:]}")
        return content


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

    @traceable(name="gemini_generation", tags=["llm", "gemini"])
    def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: dict = None,  # Ignored for Gemini (for interface compatibility)
        max_tokens: int = None
    ) -> str:
        """Generate using Gemini API."""
        import time

        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Use provided max_tokens or default to 8192
        if max_tokens is None:
            max_tokens = 8192

        start_time = time.time()
        try:
            response = self.model.generate_content(
                combined_prompt,
                generation_config={
                    "temperature": temperature,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": max_tokens,
                }
            )

            content = response.text

            # Extract JSON from reasoning output if needed
            content = self._extract_response_from_reasoning_output(content)

            # Log to both LangSmith and Langfuse
            duration_ms = (time.time() - start_time) * 1000
            log_llm_call(
                provider="gemini",
                model=self.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response=content,
                temperature=temperature,
                duration_ms=duration_ms,
            )

            return content
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_llm_call(
                provider="gemini",
                model=self.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response="",
                temperature=temperature,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise


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

    @traceable(name="claude_generation", tags=["llm", "claude"])
    def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: dict = None,
        max_tokens: int = 8192,
        thinking_budget: int = None  # Claude extended thinking
    ) -> str:
        """Generate using Claude API with optional extended thinking."""
        import time

        # Build request parameters
        request_params = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        # Add extended thinking if budget specified (Claude feature)
        if thinking_budget and "claude" in self.model_name.lower():
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget  # e.g., 2000-10000
            }
            print(f"[DEBUG Claude] Using extended thinking with {thinking_budget} token budget")

        start_time = time.time()
        try:
            message = self.client.messages.create(**request_params)

            content = message.content[0].text

            # Extract JSON from reasoning output if needed
            content = self._extract_response_from_reasoning_output(content)

            # Log to both LangSmith and Langfuse
            duration_ms = (time.time() - start_time) * 1000
            log_llm_call(
                provider="claude",
                model=self.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response=content,
                temperature=temperature,
                duration_ms=duration_ms,
            )

            return content
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_llm_call(
                provider="claude",
                model=self.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response="",
                temperature=temperature,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise


class CustomLLMClient(LLMClient):
    """Custom LLM API client (OpenAI-compatible)."""

    def __init__(self, model_name: Optional[str] = None):
        """Initialize custom LLM client."""
        try:
            from openai import OpenAI
            import httpx
        except ImportError:
            raise ImportError(
                "Required packages not installed. "
                "Install with: pip install openai httpx"
            )

        api_key = os.getenv("CUSTOM_LLM_API_KEY")
        base_url = os.getenv("CUSTOM_LLM_BASE_URL")

        if not api_key:
            raise ValueError("CUSTOM_LLM_API_KEY not found in environment variables")
        if not base_url:
            raise ValueError("CUSTOM_LLM_BASE_URL not found in environment variables")

        # Create a custom httpx client with event hooks to modify headers
        def add_api_key_header(request: httpx.Request):
            """Event hook to add X-API-Key header and remove Authorization."""
            # Remove Authorization header if present (OpenAI SDK adds this by default)
            if "Authorization" in request.headers:
                del request.headers["Authorization"]
            # Add X-API-Key header for vLLM authentication
            request.headers["X-API-Key"] = api_key

        # Create custom httpx client with request hook
        http_client = httpx.Client(
            event_hooks={"request": [add_api_key_header]}
        )

        # Create OpenAI client with custom http client
        self.client = OpenAI(
            api_key="dummy",  # Dummy value - will be removed by hook
            base_url=base_url,
            http_client=http_client
        )
        self.model_name = model_name or os.getenv("CUSTOM_LLM_MODEL", "default-model")

    @traceable(name="custom_llm_generation", tags=["llm", "custom"])
    def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: dict = None,
        max_tokens: int = None,  # Auto-calculate if None
        max_retries: int = None,  # Max retry attempts for 503 errors (from env)
        initial_retry_delay: float = None  # Initial delay in seconds (from env)
    ) -> str:
        """Generate using custom LLM API with optional structured output and retry logic."""
        import time
        from openai import APIStatusError

        start_time = time.time()

        # Get retry settings from environment variables
        if max_retries is None:
            max_retries = int(os.getenv("CUSTOM_LLM_MAX_RETRIES", "5"))
        if initial_retry_delay is None:
            initial_retry_delay = float(os.getenv("CUSTOM_LLM_INITIAL_RETRY_DELAY", "5.0"))

        # Estimate input tokens (rough approximation: 1 token ≈ 4 characters)
        input_text = system_prompt + user_prompt
        estimated_input_tokens = len(input_text) // 4

        # Get model context limit from environment or use default
        model_context_limit = int(os.getenv("CUSTOM_LLM_CONTEXT_LIMIT", "32768"))

        # Calculate safe max_tokens if not provided
        if max_tokens is None:
            # Leave 20% buffer for tokenization differences and safety
            available_tokens = model_context_limit - estimated_input_tokens
            max_tokens = int(available_tokens * 0.8)
            # Ensure it's within reasonable bounds
            max_tokens = max(512, min(max_tokens, 16384))
            print(f"[DEBUG CustomLLM] Auto-calculated max_tokens: {max_tokens} "
                  f"(estimated input: {estimated_input_tokens}, limit: {model_context_limit})")
        else:
            # Validate provided max_tokens doesn't exceed available space
            available_tokens = model_context_limit - estimated_input_tokens
            if max_tokens > available_tokens:
                print(f"[WARNING CustomLLM] Requested max_tokens ({max_tokens}) exceeds available space ({available_tokens})")
                max_tokens = max(512, int(available_tokens * 0.8))
                print(f"[WARNING CustomLLM] Adjusted max_tokens to: {max_tokens}")

        # Build request parameters
        request_params = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Add response_format if provided (for structured output)
        if response_format:
            request_params["response_format"] = response_format
            print(f"[DEBUG CustomLLM] Using structured output with response_format")

        print(f"[DEBUG CustomLLM] Requesting max_tokens: {max_tokens}")

        # Retry loop for handling 503 errors (server warm-up)
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(**request_params)
                # Success! Break out of retry loop
                break
            except APIStatusError as e:
                last_error = e
                # Check if it's a 503 (service unavailable) - server warming up
                if e.status_code == 503:
                    if attempt < max_retries - 1:
                        # Calculate exponential backoff delay
                        delay = initial_retry_delay * (2 ** attempt)
                        print(f"\n{'='*60}")
                        print(f"[INFO] vLLM server is warming up (503 error)")
                        print(f"[INFO] Attempt {attempt + 1}/{max_retries}")
                        print(f"[INFO] Retrying in {delay:.1f} seconds...")
                        print(f"{'='*60}\n")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"\n{'='*60}")
                        print(f"[ERROR] vLLM server still unavailable after {max_retries} attempts")
                        print(f"[ERROR] The server may need more time to warm up")
                        print(f"[ERROR] Please wait a minute and try again")
                        print(f"{'='*60}\n")
                        raise Exception(
                            f"vLLM server unavailable after {max_retries} attempts. "
                            f"The server is still warming up. Please wait a minute and try again."
                        ) from e
                else:
                    # Not a 503 error, re-raise immediately
                    print(f"\n{'='*60}")
                    print(f"[ERROR] vLLM API Error (HTTP {e.status_code})")
                    print(f"[ERROR] Message: {str(e)}")
                    print(f"[ERROR] Check your CUSTOM_LLM_BASE_URL and CUSTOM_LLM_API_KEY")
                    print(f"{'='*60}\n")
                    raise
            except Exception as e:
                # Connection and other non-API errors
                print(f"\n{'='*60}")
                print(f"[ERROR] Connection Error to vLLM Server")
                print(f"[ERROR] Error type: {type(e).__name__}")
                print(f"[ERROR] Error message: {str(e)}")
                print(f"[ERROR] Base URL: {base_url}")
                print(f"[ERROR] \nPossible causes:")
                print(f"[ERROR] 1. vLLM server is not running or has been stopped")
                print(f"[ERROR] 2. Invalid or expired CUSTOM_LLM_BASE_URL")
                print(f"[ERROR] 3. Invalid CUSTOM_LLM_API_KEY")
                print(f"[ERROR] 4. Network connectivity issue")
                print(f"[ERROR] \nSolution: Switch to 'gemini' provider in the sidebar")
                print(f"{'='*60}\n")
                # Non-API errors are not retried
                raise
        else:
            # This shouldn't happen, but just in case
            if last_error:
                raise last_error
            raise Exception("Unknown error during API call")

        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason

        # Debug: Show finish reason and response stats
        print(f"[DEBUG CustomLLM] finish_reason: {finish_reason}")
        print(f"[DEBUG CustomLLM] Response length: {len(content)} chars (~{len(content)//4} tokens)")

        # Check for suspiciously short structured output responses
        if response_format and finish_reason == "stop" and len(content) < 2000:
            print(f"\n{'='*60}")
            print(f"[WARNING] INCOMPLETE STRUCTURED OUTPUT DETECTED")
            print(f"{'='*60}")
            print(f"Response is suspiciously short ({len(content)} chars) for structured output.")
            print(f"This model may not support structured output well.")
            print(f"\nRECOMMENDATIONS:")
            print(f"1. Switch to Gemini (gemini-2.0-flash-exp) - BEST OPTION")
            print(f"2. Switch to Claude (claude-sonnet-4-5) - EXCELLENT")
            print(f"3. Use a larger model (DeepSeek-V3, not R1-1.5B)")
            print(f"4. Check vLLM server --max-model-len configuration")
            print(f"{'='*60}\n")

        # Check if response was truncated
        if finish_reason == "length":
            estimated_tokens = len(content) // 4
            print(f"\n{'='*60}")
            print(f"[ERROR] RESPONSE TRUNCATED BY SERVER")
            print(f"{'='*60}")
            print(f"Requested: {max_tokens} tokens")
            print(f"Received: ~{estimated_tokens} tokens (~{len(content)} chars)")
            print(f"\nThis is a vLLM server limitation, NOT a client issue.")
            print(f"\nRECOMMENDATIONS:")
            print(f"1. Switch to Gemini or Claude (no truncation issues)")
            print(f"2. Reconfigure vLLM with higher --max-model-len")
            print(f"3. Use a larger model (DeepSeek-V3 instead of R1-1.5B)")
            print(f"{'='*60}\n")

            # For now, try to salvage what we have by adding closing braces
            if not content.rstrip().endswith('}'):
                print(f"[INFO] Attempting to repair truncated JSON...")
                # This is a hack but might help in some cases
                content = content.rstrip()
                # Count open vs closed braces
                open_braces = content.count('{')
                close_braces = content.count('}')
                if open_braces > close_braces:
                    # Try to close the JSON
                    content += '\n}' * (open_braces - close_braces)
                    print(f"[INFO] Added {open_braces - close_braces} closing braces")

        # Debug: Show original response length (handle encoding safely)
        try:
            print(f"[DEBUG CustomLLM] Raw response length: {len(content)} chars")
            print(f"[DEBUG CustomLLM] Response starts with: {content[:200]}")
        except UnicodeEncodeError:
            print(f"[DEBUG CustomLLM] Raw response length: {len(content)} chars")
            print(f"[DEBUG CustomLLM] Response starts with: [Unicode content - cannot display]")

        # Post-process response to extract actual output from reasoning models
        content = self._extract_response_from_reasoning_output(content)

        try:
            print(f"[DEBUG CustomLLM] After extraction: {len(content)} chars")
            print(f"[DEBUG CustomLLM] Extracted starts with: {content[:200]}")
        except UnicodeEncodeError:
            print(f"[DEBUG CustomLLM] After extraction: {len(content)} chars")
            print(f"[DEBUG CustomLLM] Extracted starts with: [Unicode content - cannot display]")

        # Log to both LangSmith and Langfuse
        duration_ms = (time.time() - start_time) * 1000
        log_llm_call(
            provider="custom",
            model=self.model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=content,
            temperature=temperature,
            duration_ms=duration_ms,
        )

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
        print(f"[DEBUG EXTRACTION] json_start position: {json_start}")

        # Also check for common markers that might indicate where JSON starts
        json_markers = [
            'json\n{', 'JSON:\n{', '```json',
            'Here is the JSON', 'Here\'s the JSON',
            'The JSON response', 'Final response:',
            '"score":', "'score':"
        ]
        for marker in json_markers:
            marker_pos = content.lower().find(marker.lower())
            if marker_pos != -1:
                print(f"[DEBUG EXTRACTION] Found marker '{marker}' at position {marker_pos}")
                # Look for { after this marker
                temp_start = content.find('{', marker_pos)
                if temp_start != -1 and (json_start == -1 or temp_start < json_start):
                    json_start = temp_start
                    print(f"[DEBUG EXTRACTION] Updated json_start to {json_start}")

        if json_start != -1:
            # Find the matching closing brace
            json_end = content.rfind('}')
            print(f"[DEBUG EXTRACTION] json_end position: {json_end}")
            if json_end != -1 and json_end > json_start:
                potential_json = content[json_start:json_end + 1]
                print(f"[DEBUG EXTRACTION] Potential JSON length: {len(potential_json)} chars")
                print("[DEBUG EXTRACTION] Contains 'score':", '"score"' in potential_json)
                print("[DEBUG EXTRACTION] Contains 'analysis':", '"analysis"' in potential_json)
                print("[DEBUG EXTRACTION] Contains 'suggestions':", '"suggestions"' in potential_json)
                # Verify it looks like valid JSON structure
                if '"score"' in potential_json or '"analysis"' in potential_json or '"suggestions"' in potential_json:
                    print(f"[DEBUG] Extracted JSON from mixed content (full match), length: {len(potential_json)} chars")
                    return potential_json
                else:
                    print(f"[DEBUG EXTRACTION] Potential JSON failed validation check")
                    print(f"[DEBUG EXTRACTION] First 500 chars: {potential_json[:500]}")

        # Fallback: Try regex approach for complex cases
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            potential_json = json_match.group(0)
            # Verify it looks like valid JSON structure
            if '"score"' in potential_json or '"analysis"' in potential_json:
                print(f"[DEBUG] Extracted JSON from mixed content (regex), length: {len(potential_json)} chars")
                return potential_json

        # Method 3: No special handling needed
        print(f"[DEBUG] No JSON extraction needed, returning original content")
        return content


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
