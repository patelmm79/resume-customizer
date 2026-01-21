#!/usr/bin/env python3
"""Test script for cloud storage settings implementation."""

import os
import sys
import json
from pathlib import Path

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.settings import (
    load_settings,
    save_settings,
    get_settings_source,
    get_saved_llm_config,
    set_saved_llm_config,
    DEFAULT_SETTINGS,
)


def test_local_fallback():
    """Test that local settings work when cloud storage is not configured."""
    print("\n" + "=" * 60)
    print("TEST 1: Local Storage (No Cloud Config)")
    print("=" * 60)

    # Ensure cloud config is not set
    for key in ["RESUME_SETTINGS_STORAGE", "RESUME_SETTINGS_BUCKET"]:
        os.environ.pop(key, None)

    print("\n✓ Cloud storage not configured")

    # Test load (should use defaults or local file)
    settings = load_settings()
    print(f"✓ Loaded settings: {json.dumps(settings, indent=2)}")

    # Get source
    source = get_settings_source()
    print(f"✓ Storage source: {source}")

    # Test save
    test_settings = DEFAULT_SETTINGS.copy()
    test_settings["candidate_name"] = "Test_Candidate_Local"
    if save_settings(test_settings):
        print("✓ Settings saved to local storage")

        # Load again to verify
        loaded = load_settings()
        assert loaded["candidate_name"] == "Test_Candidate_Local"
        print("✓ Settings persisted correctly")
    else:
        print("✗ Failed to save settings")
        return False

    return True


def test_cloud_config_detection():
    """Test that cloud storage configuration is detected."""
    print("\n" + "=" * 60)
    print("TEST 2: Cloud Config Detection (No Credentials)")
    print("=" * 60)

    # Set cloud config but don't set actual credentials
    os.environ["RESUME_SETTINGS_STORAGE"] = "s3"
    os.environ["RESUME_SETTINGS_BUCKET"] = "test-bucket"

    print("\n✓ Cloud storage config set (S3)")

    # Get source should show S3 bucket
    source = get_settings_source()
    print(f"✓ Storage source: {source}")
    assert "S3" in source and "test-bucket" in source

    # Load should fall back to local (since no credentials)
    settings = load_settings()
    print(f"✓ Loaded settings (with fallback): {json.dumps(settings, indent=2)}")

    # Save should attempt cloud, then fall back to local
    test_settings = DEFAULT_SETTINGS.copy()
    test_settings["candidate_name"] = "Test_Candidate_S3_Fallback"
    if save_settings(test_settings):
        print("✓ Settings saved (with fallback)")
    else:
        print("✗ Failed to save settings")
        return False

    # Clean up
    os.environ.pop("RESUME_SETTINGS_STORAGE", None)
    os.environ.pop("RESUME_SETTINGS_BUCKET", None)

    return True


def test_settings_source_display():
    """Test that settings source is displayed correctly."""
    print("\n" + "=" * 60)
    print("TEST 3: Settings Source Display")
    print("=" * 60)

    # Test local source
    os.environ.pop("RESUME_SETTINGS_STORAGE", None)
    os.environ.pop("RESUME_SETTINGS_BUCKET", None)

    source = get_settings_source()
    print(f"\n✓ Local source: {source}")

    # Test S3 source (configured but no credentials)
    os.environ["RESUME_SETTINGS_STORAGE"] = "s3"
    os.environ["RESUME_SETTINGS_BUCKET"] = "my-bucket"

    source = get_settings_source()
    print(f"✓ S3 source: {source}")
    assert "S3" in source

    # Test GCS source
    os.environ["RESUME_SETTINGS_STORAGE"] = "gcs"
    os.environ["RESUME_SETTINGS_BUCKET"] = "my-gcs-bucket"

    source = get_settings_source()
    print(f"✓ GCS source: {source}")
    assert "GCS" in source

    # Clean up
    os.environ.pop("RESUME_SETTINGS_STORAGE", None)
    os.environ.pop("RESUME_SETTINGS_BUCKET", None)

    return True


def test_llm_config():
    """Test LLM provider and model settings."""
    print("\n" + "=" * 60)
    print("TEST 4: LLM Provider Settings")
    print("=" * 60)

    # Clean environment
    os.environ.pop("RESUME_SETTINGS_STORAGE", None)
    os.environ.pop("RESUME_SETTINGS_BUCKET", None)

    # Test default LLM config
    config = get_saved_llm_config()
    print(f"\n✓ Default LLM config: {config}")
    assert config["provider"] == "gemini"

    # Test saving LLM config
    if set_saved_llm_config("claude", "claude-3-5-sonnet-20241022"):
        print("✓ Saved Claude model")

        # Load and verify
        loaded_config = get_saved_llm_config()
        print(f"✓ Loaded LLM config: {loaded_config}")
        assert loaded_config["provider"] == "claude"
        assert loaded_config["model"] == "claude-3-5-sonnet-20241022"
    else:
        print("✗ Failed to save LLM config")
        return False

    # Test switching provider
    if set_saved_llm_config("custom", "llama3:70b"):
        print("✓ Saved custom model")

        loaded_config = get_saved_llm_config()
        assert loaded_config["provider"] == "custom"
        assert loaded_config["model"] == "llama3:70b"
    else:
        print("✗ Failed to save custom model")
        return False

    # Reset to defaults
    if set_saved_llm_config("gemini", None):
        print("✓ Reset to Gemini defaults")
        config = get_saved_llm_config()
        assert config["provider"] == "gemini"
    else:
        print("✗ Failed to reset")
        return False

    return True


def main():
    """Run all tests."""
    print("Resume Customizer - Cloud Settings Tests")
    print("=" * 60)

    tests = [
        ("Local Fallback", test_local_fallback),
        ("Cloud Config Detection", test_cloud_config_detection),
        ("Settings Source Display", test_settings_source_display),
        ("LLM Config", test_llm_config),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
