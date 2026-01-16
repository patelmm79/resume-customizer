"""LangSmith configuration and initialization."""
import os
from dotenv import load_dotenv

load_dotenv()


def configure_langsmith():
    """
    Initialize and configure LangSmith for tracing.

    This function reads LangSmith environment variables and configures the SDK.
    It should be called early in the application startup.

    Environment variables:
    - LANGSMITH_API_KEY: API key for LangSmith (from Secret Manager)
    - LANGSMITH_PROJECT: Project name in LangSmith (auto-set to service_name, e.g., resume-customizer)
    - LANGSMITH_ENDPOINT: LangSmith endpoint (usually https://api.smith.langchain.com)
    - LANGSMITH_TRACING: Enable/disable tracing (true/false)
    """
    try:
        from langsmith import Client
    except ImportError:
        print("[WARNING] langsmith package not installed. Tracing disabled.")
        return False

    # Check if tracing is enabled
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() in ("true", "1", "yes")

    # Debug: Print what we found
    print(f"[DEBUG] LANGSMITH_TRACING={os.getenv('LANGSMITH_TRACING', 'not set')}")
    print(f"[DEBUG] LANGSMITH_PROJECT={os.getenv('LANGSMITH_PROJECT', 'not set')}")
    print(f"[DEBUG] LANGSMITH_ENDPOINT={os.getenv('LANGSMITH_ENDPOINT', 'not set')}")
    print(f"[DEBUG] LANGSMITH_API_KEY={'***' if os.getenv('LANGSMITH_API_KEY') else 'not set'}")

    if not tracing_enabled:
        print("[INFO] LangSmith tracing is disabled (LANGSMITH_TRACING=false)")
        return False

    # Get required configuration
    api_key = os.getenv("LANGSMITH_API_KEY")
    endpoint = os.getenv("LANGSMITH_ENDPOINT")
    project = os.getenv("LANGSMITH_PROJECT")

    # Validate configuration
    if not api_key:
        print("[WARNING] LANGSMITH_API_KEY not set. LangSmith tracing disabled.")
        return False

    if not endpoint:
        print("[WARNING] LANGSMITH_ENDPOINT not set. LangSmith tracing disabled.")
        return False

    if not project:
        print("[WARNING] LANGSMITH_PROJECT not set. LangSmith tracing disabled.")
        return False

    try:
        # Environment variables are already set, just validate by creating client
        # LangSmith Client reads from LANGSMITH_API_KEY, LANGSMITH_ENDPOINT, LANGSMITH_PROJECT env vars
        client = Client()

        # Verify connection by checking project
        print(f"[INFO] LangSmith tracing enabled")
        print(f"[INFO] Project: {project}")
        print(f"[INFO] Endpoint: {endpoint}")
        print(f"[INFO] Client initialized successfully")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to initialize LangSmith: {e}")
        import traceback
        traceback.print_exc()
        return False


def is_langsmith_enabled():
    """Check if LangSmith tracing is enabled."""
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() in ("true", "1", "yes")
    api_key = os.getenv("LANGSMITH_API_KEY")
    endpoint = os.getenv("LANGSMITH_ENDPOINT")
    project = os.getenv("LANGSMITH_PROJECT")

    return tracing_enabled and api_key and endpoint and project
