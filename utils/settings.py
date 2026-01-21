"""Application settings management for Resume Customizer."""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


SETTINGS_FILE = Path(__file__).parent.parent / ".settings.json"

DEFAULT_SETTINGS = {
    "candidate_name": "Optimized_Resume",
    "pdf_font_size": 9.5,
    "pdf_line_height": 1.2,
    "pdf_page_margin": 0.75,
}


def load_settings() -> Dict[str, Any]:
    """
    Load settings from file.

    Returns:
        Dictionary of settings, or defaults if file doesn't exist
    """
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys are present
                merged = DEFAULT_SETTINGS.copy()
                merged.update(settings)
                return merged
        except Exception as e:
            print(f"[WARNING] Failed to load settings: {e}")
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save settings to file.

    Args:
        settings: Dictionary of settings to save

    Returns:
        True if successful, False otherwise
    """
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
