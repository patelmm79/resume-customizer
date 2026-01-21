"""Application settings management for Resume Customizer.

Supports cloud storage with local fallback:
1. Cloud Storage (S3, GCS) - persists across deployments
2. Local .settings.json file - for development
3. Built-in defaults - fallback

Cloud configuration via environment variables:
- RESUME_SETTINGS_STORAGE: 's3', 'gcs', or 'local' (default: 'local')
- RESUME_SETTINGS_BUCKET: Cloud bucket name
- RESUME_SETTINGS_KEY: Path/key in bucket (default: '.settings.json')
- AWS_REGION / GOOGLE_CLOUD_PROJECT: Cloud-specific config
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Local file fallback
SETTINGS_FILE = Path(__file__).parent.parent / ".settings.json"

DEFAULT_SETTINGS = {
    # Candidate Information
    "candidate_name": "Optimized_Resume",

    # PDF Formatting
    "pdf_font_size": 9.5,
    "pdf_line_height": 1.2,
    "pdf_page_margin": 0.75,

    # LLM Configuration
    "llm_provider": "gemini",  # Options: 'gemini', 'claude', 'custom'
    "llm_model": None,  # None = use provider default. Can be overridden by GEMINI_MODEL, CLAUDE_MODEL, etc env vars
}


def _get_storage_type() -> str:
    """Determine which storage to use."""
    return os.getenv("RESUME_SETTINGS_STORAGE", "local").lower()


def _get_cloud_client():
    """Initialize cloud storage client based on configuration."""
    storage_type = _get_storage_type()

    if storage_type == "s3":
        try:
            import boto3
            return boto3.client('s3')
        except ImportError:
            print("[WARNING] boto3 not installed. Falling back to local storage.")
            return None
    elif storage_type == "gcs":
        try:
            from google.cloud import storage
            return storage.Client()
        except ImportError:
            print("[WARNING] google-cloud-storage not installed. Falling back to local storage.")
            return None

    return None


def _load_from_cloud() -> Optional[Dict[str, Any]]:
    """Load settings from cloud storage."""
    storage_type = _get_storage_type()
    bucket_name = os.getenv("RESUME_SETTINGS_BUCKET")
    settings_key = os.getenv("RESUME_SETTINGS_KEY", ".settings.json")

    if not bucket_name:
        return None

    try:
        if storage_type == "s3":
            import boto3
            s3_client = boto3.client('s3')
            response = s3_client.get_object(Bucket=bucket_name, Key=settings_key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)

        elif storage_type == "gcs":
            from google.cloud import storage
            gcs_client = storage.Client()
            bucket = gcs_client.bucket(bucket_name)
            blob = bucket.blob(settings_key)
            if blob.exists():
                return json.loads(blob.download_as_string().decode('utf-8'))

    except Exception as e:
        print(f"[WARNING] Failed to load from cloud storage ({storage_type}): {e}")
        return None

    return None


def _save_to_cloud(settings: Dict[str, Any]) -> bool:
    """Save settings to cloud storage."""
    storage_type = _get_storage_type()
    bucket_name = os.getenv("RESUME_SETTINGS_BUCKET")
    settings_key = os.getenv("RESUME_SETTINGS_KEY", ".settings.json")

    if not bucket_name:
        return False

    try:
        content = json.dumps(settings, indent=2)

        if storage_type == "s3":
            import boto3
            s3_client = boto3.client('s3')
            s3_client.put_object(
                Bucket=bucket_name,
                Key=settings_key,
                Body=content,
                ContentType='application/json'
            )
            return True

        elif storage_type == "gcs":
            from google.cloud import storage
            gcs_client = storage.Client()
            bucket = gcs_client.bucket(bucket_name)
            blob = bucket.blob(settings_key)
            blob.upload_from_string(content, content_type='application/json')
            return True

    except Exception as e:
        print(f"[WARNING] Failed to save to cloud storage ({storage_type}): {e}")
        return False

    return False


def load_settings() -> Dict[str, Any]:
    """
    Load settings from cloud storage or local file.

    Priority order:
    1. Cloud Storage (if configured and available)
    2. Local .settings.json file
    3. Built-in defaults

    Returns:
        Dictionary of settings merged from all available sources
    """
    # Start with defaults
    settings = DEFAULT_SETTINGS.copy()

    # Try cloud storage first
    storage_type = _get_storage_type()
    if storage_type in ("s3", "gcs"):
        cloud_settings = _load_from_cloud()
        if cloud_settings:
            settings.update(cloud_settings)
            return settings

    # Fall back to local file
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                file_settings = json.load(f)
                settings.update(file_settings)
        except Exception as e:
            print(f"[WARNING] Failed to load local settings file: {e}")

    return settings


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save settings to cloud storage or local file.

    Attempts cloud storage first, then falls back to local file.

    Args:
        settings: Dictionary of settings to save

    Returns:
        True if successful, False otherwise
    """
    storage_type = _get_storage_type()

    # Try cloud storage first
    if storage_type in ("s3", "gcs"):
        if _save_to_cloud(settings):
            return True
        # Fall through to local save as backup

    # Save to local file
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save settings: {e}")
        return False


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a single setting value.

    Args:
        key: Setting key
        default: Default value if not found

    Returns:
        Setting value or default
    """
    settings = load_settings()
    return settings.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """
    Set a single setting value.

    Args:
        key: Setting key
        value: Setting value

    Returns:
        True if successful, False otherwise
    """
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)


def get_settings_source() -> str:
    """
    Get the current settings storage source (for UI display).

    Returns:
        String describing where settings are loaded from
    """
    storage_type = _get_storage_type()

    if storage_type in ("s3", "gcs"):
        bucket = os.getenv("RESUME_SETTINGS_BUCKET")
        if bucket:
            return f"{storage_type.upper()} Bucket: {bucket}"
        return f"{storage_type.upper()} (not configured)"

    if SETTINGS_FILE.exists():
        return "Local File (.settings.json)"

    return "Defaults"


def get_saved_llm_config() -> Dict[str, Any]:
    """
    Get saved LLM provider and model from settings.

    Returns:
        Dictionary with 'provider' and 'model' keys
    """
    settings = load_settings()
    return {
        "provider": settings.get("llm_provider", "gemini"),
        "model": settings.get("llm_model"),
    }


def set_saved_llm_config(provider: str, model: Optional[str] = None) -> bool:
    """
    Save LLM provider and model selection to settings.

    Args:
        provider: LLM provider ('gemini', 'claude', 'custom')
        model: Optional specific model name

    Returns:
        True if successful, False otherwise
    """
    settings = load_settings()
    settings["llm_provider"] = provider
    settings["llm_model"] = model
    return save_settings(settings)
