"""Test JSON extraction across all LLM providers."""
import os
from dotenv import load_dotenv

load_dotenv()


def test_custom_llm():
    """Test CustomLLM with DeepSeek R1."""
    try:
        from utils.llm_client import CustomLLMClient

        print("\n" + "="*60)
        print("Testing CustomLLM (DeepSeek R1)")
        print("="*60)

        client = CustomLLMClient()

        response = client.generate_with_system_prompt(
            system_prompt="You are a helpful assistant that returns JSON.",
            user_prompt='Return this JSON: {"score": 85, "test": "success"}',
            temperature=0.3
        )

        print(f"\nFinal response length: {len(response)} chars")
        print(f"Response: {response[:500]}")

        # Try to parse
        import json
        parsed = json.loads(response)
        print(f"\n[SUCCESS] CustomLLM JSON parsed: score={parsed.get('score')}")
        return True

    except Exception as e:
        print(f"\n[FAILED] CustomLLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gemini_llm():
    """Test GeminiClient from llm_client.py."""
    try:
        from utils.llm_client import GeminiClient

        print("\n" + "="*60)
        print("Testing GeminiClient (from llm_client.py)")
        print("="*60)

        client = GeminiClient()

        response = client.generate_with_system_prompt(
            system_prompt="You are a helpful assistant that returns JSON.",
            user_prompt='Return this JSON: {"score": 90, "test": "gemini"}',
            temperature=0.3
        )

        print(f"\nFinal response length: {len(response)} chars")
        print(f"Response: {response[:500]}")

        # Try to parse
        import json
        parsed = json.loads(response)
        print(f"\n[SUCCESS] GeminiClient JSON parsed: score={parsed.get('score')}")
        return True

    except Exception as e:
        print(f"\n[FAILED] GeminiClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_legacy_gemini():
    """Test legacy GeminiClient from gemini_client.py."""
    try:
        from utils.gemini_client import GeminiClient

        print("\n" + "="*60)
        print("Testing Legacy GeminiClient (from gemini_client.py)")
        print("="*60)

        client = GeminiClient()

        response = client.generate_with_system_prompt(
            system_prompt="You are a helpful assistant that returns JSON.",
            user_prompt='Return this JSON: {"score": 95, "test": "legacy"}',
            temperature=0.3
        )

        print(f"\nFinal response length: {len(response)} chars")
        print(f"Response: {response[:500]}")

        # Try to parse
        import json
        parsed = json.loads(response)
        print(f"\n[SUCCESS] Legacy GeminiClient JSON parsed: score={parsed.get('score')}")
        return True

    except Exception as e:
        print(f"\n[FAILED] Legacy GeminiClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing JSON extraction across all LLM providers...")

    results = []

    # Test CustomLLM (DeepSeek R1)
    if os.getenv("CUSTOM_LLM_API_KEY"):
        results.append(("CustomLLM", test_custom_llm()))
    else:
        print("\n[SKIP] CustomLLM - no API key")

    # Test GeminiClient
    if os.getenv("GEMINI_API_KEY"):
        results.append(("GeminiClient", test_gemini_llm()))
        results.append(("Legacy Gemini", test_legacy_gemini()))
    else:
        print("\n[SKIP] Gemini - no API key")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {name}")

    all_passed = all(success for _, success in results)
    exit(0 if all_passed else 1)
