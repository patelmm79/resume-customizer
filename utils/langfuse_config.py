"""Langfuse configuration and initialization."""
import os
from dotenv import load_dotenv

load_dotenv()


def configure_langfuse():
    """
    Initialize and configure Langfuse for tracing.

    This function reads Langfuse environment variables and configures the SDK.
    It should be called early in the application startup.

    Environment variables:
    - LANGFUSE_PUBLIC_KEY: Public key for Langfuse
    - LANGFUSE_SECRET_KEY: Secret key for Langfuse
    - LANGFUSE_HOST: Langfuse host (optional, defaults to https://cloud.langfuse.com)
    - LANGFUSE_ENABLED: Enable/disable Langfuse tracing (true/false)
    """
    try:
        from langfuse import Langfuse
    except ImportError:
        print("[WARNING] langfuse package not installed. Langfuse tracing disabled.")
        return None

    # Load environment variables from .env file (in case they're there)
    load_dotenv()

    # Check if tracing is enabled
    enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() in ("true", "1", "yes")

    # Debug: Print what we found
    all_env_vars = os.environ.copy()
    print(f"[DEBUG] All env vars starting with LANGFUSE: {[(k, '***' if len(v) > 0 else 'empty') for k, v in all_env_vars.items() if k.startswith('LANGFUSE')]}")
    print(f"[DEBUG] LANGFUSE_ENABLED={os.getenv('LANGFUSE_ENABLED', 'not set')}")
    print(f"[DEBUG] LANGFUSE_PUBLIC_KEY={'***' if os.getenv('LANGFUSE_PUBLIC_KEY') else 'not set'}")
    print(f"[DEBUG] LANGFUSE_SECRET_KEY={'***' if os.getenv('LANGFUSE_SECRET_KEY') else 'not set'}")
    print(f"[DEBUG] LANGFUSE_HOST={os.getenv('LANGFUSE_HOST', 'not set (using default)')}")

    if not enabled:
        print("[INFO] Langfuse tracing is disabled (LANGFUSE_ENABLED=false)")
        return None

    # Get required configuration
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # Validate configuration
    if not public_key:
        print("[WARNING] LANGFUSE_PUBLIC_KEY not set. Langfuse tracing disabled.")
        return None

    if not secret_key:
        print("[WARNING] LANGFUSE_SECRET_KEY not set. Langfuse tracing disabled.")
        return None

    try:
        # Initialize Langfuse client
        print(f"[DEBUG] Initializing Langfuse with host: {host}")
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )

        # Client initialized
        print(f"[INFO] Langfuse client initialized successfully")
        print(f"[INFO] Host: {host}")

        return client
    except Exception as e:
        print(f"[ERROR] Failed to initialize Langfuse: {e}")
        import traceback
        traceback.print_exc()
        return None


def is_langfuse_enabled():
    """Check if Langfuse tracing is enabled."""
    enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() in ("true", "1", "yes")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    return enabled and public_key and secret_key
