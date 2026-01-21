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


def _get_default_providers() -> list:
    """
    Build default LLM providers list from actual available models.

    This reads from get_available_models() which gets models from environment variables
    (GEMINI_MODELS, CLAUDE_MODELS, CUSTOM_MODELS) or uses hardcoded defaults.

    This ensures settings.py always uses the same models as llm_client.py
    """
    from utils.llm_client import get_available_models

    available_models = get_available_models()

    providers = []

    # Gemini provider
    if "gemini" in available_models:
        providers.append({
            "name": "gemini",
            "models": available_models["gemini"],
            "api_key_env": "GEMINI_API_KEY",
            "enabled": True,
        })

    # Claude provider
    if "claude" in available_models:
        providers.append({
            "name": "claude",
            "models": available_models["claude"],
            "api_key_env": "ANTHROPIC_API_KEY",
            "enabled": True,
        })

    # Custom provider
    if "custom" in available_models:
        providers.append({
            "name": "custom",
            "models": available_models["custom"],
            "api_key_env": "CUSTOM_LLM_API_KEY",
            "enabled": False,
        })

    return providers


DEFAULT_SETTINGS = {
    # Candidate Information
    "candidate_name": "Optimized_Resume",

    # PDF Formatting
    "pdf_font_size": 9.5,
    "pdf_line_height": 1.2,
    "pdf_page_margin": 0.75,

    # LLM Provider Management - dynamically populated from available models
    "llm_providers": _get_default_providers(),
    "llm_default_provider": "gemini",
    "llm_default_model": None,  # Will be set to first available model for default provider
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
    return {
        "provider": get_default_provider(),
        "model": get_default_model(),
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
    settings["llm_default_provider"] = provider
    settings["llm_default_model"] = model
    return save_settings(settings)


def get_llm_providers() -> list:
    """
    Get list of all configured LLM providers.

    Returns:
        List of provider dictionaries with name, models, api_key_env, and enabled status
    """
    settings = load_settings()
    return settings.get("llm_providers", DEFAULT_SETTINGS.get("llm_providers", []))


def get_provider(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific LLM provider by name.

    Args:
        name: Provider name

    Returns:
        Provider dictionary or None if not found
    """
    providers = get_llm_providers()
    for provider in providers:
        if provider["name"] == name:
            return provider
    return None


def add_provider(name: str, models: list, api_key_env: str, enabled: bool = True) -> bool:
    """
    Add a new LLM provider to settings.

    Args:
        name: Provider name (unique identifier)
        models: List of model names available for this provider
        api_key_env: Environment variable name for API key
        enabled: Whether provider is enabled by default

    Returns:
        True if successful, False otherwise
    """
    settings = load_settings()

    # Check if provider already exists
    for provider in settings.get("llm_providers", []):
        if provider["name"] == name:
            return False  # Provider already exists

    # Add new provider
    new_provider = {
        "name": name,
        "models": models,
        "api_key_env": api_key_env,
        "enabled": enabled,
    }
    settings["llm_providers"].append(new_provider)

    return save_settings(settings)


def update_provider(name: str, models: Optional[list] = None,
                   api_key_env: Optional[str] = None,
                   enabled: Optional[bool] = None) -> bool:
    """
    Update an existing LLM provider.

    Args:
        name: Provider name
        models: Optional new list of models
        api_key_env: Optional new API key environment variable name
        enabled: Optional new enabled status

    Returns:
        True if successful, False otherwise
    """
    settings = load_settings()

    for provider in settings.get("llm_providers", []):
        if provider["name"] == name:
            if models is not None:
                provider["models"] = models
            if api_key_env is not None:
                provider["api_key_env"] = api_key_env
            if enabled is not None:
                provider["enabled"] = enabled
            return save_settings(settings)

    return False  # Provider not found


def delete_provider(name: str) -> bool:
    """
    Delete an LLM provider from settings.

    Args:
        name: Provider name

    Returns:
        True if successful, False otherwise
    """
    settings = load_settings()
    original_count = len(settings.get("llm_providers", []))

    settings["llm_providers"] = [
        p for p in settings.get("llm_providers", [])
        if p["name"] != name
    ]

    # If we deleted the default provider, reset to first available
    if settings.get("llm_default_provider") == name:
        if settings["llm_providers"]:
            settings["llm_default_provider"] = settings["llm_providers"][0]["name"]
            settings["llm_default_model"] = settings["llm_providers"][0]["models"][0]
        else:
            settings["llm_default_provider"] = None
            settings["llm_default_model"] = None

    if len(settings.get("llm_providers", [])) < original_count:
        return save_settings(settings)

    return False  # Provider not found


def add_model(provider_name: str, model: str) -> bool:
    """
    Add a model to an existing provider.

    Args:
        provider_name: Provider name
        model: Model name to add

    Returns:
        True if successful, False otherwise
    """
    settings = load_settings()

    for provider in settings.get("llm_providers", []):
        if provider["name"] == provider_name:
            if model not in provider["models"]:
                provider["models"].append(model)
                return save_settings(settings)
            return False  # Model already exists

    return False  # Provider not found


def remove_model(provider_name: str, model: str) -> bool:
    """
    Remove a model from a provider.

    Args:
        provider_name: Provider name
        model: Model name to remove

    Returns:
        True if successful, False otherwise
    """
    settings = load_settings()

    for provider in settings.get("llm_providers", []):
        if provider["name"] == provider_name:
            if model in provider["models"]:
                provider["models"].remove(model)

                # If this was the default model, reset to first model
                if settings.get("llm_default_model") == model and settings.get("llm_default_provider") == provider_name:
                    if provider["models"]:
                        settings["llm_default_model"] = provider["models"][0]
                    else:
                        settings["llm_default_model"] = None

                return save_settings(settings)
            return False  # Model not found

    return False  # Provider not found


def set_default_provider(name: str, model: Optional[str] = None) -> bool:
    """
    Set the default LLM provider.

    Args:
        name: Provider name
        model: Optional specific model to set as default

    Returns:
        True if successful, False otherwise
    """
    provider = get_provider(name)
    if not provider:
        return False

    settings = load_settings()
    settings["llm_default_provider"] = name

    if model:
        if model not in provider["models"]:
            return False
        settings["llm_default_model"] = model
    else:
        # Use first model as default
        settings["llm_default_model"] = provider["models"][0] if provider["models"] else None

    return save_settings(settings)


def get_default_provider() -> Optional[str]:
    """Get the default LLM provider name."""
    settings = load_settings()
    return settings.get("llm_default_provider", "gemini")


def get_default_model() -> Optional[str]:
    """
    Get the default LLM model name.

    If not explicitly set, returns the first available model for the default provider.
    """
    settings = load_settings()
    default_model = settings.get("llm_default_model")

    # If no default model set, get first model from default provider
    if not default_model:
        default_provider = settings.get("llm_default_provider", "gemini")
        provider = get_provider(default_provider)
        if provider and provider.get("models"):
            default_model = provider["models"][0]

    return default_model
