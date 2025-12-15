"""Test reasoning model output extraction."""
import os
from dotenv import load_dotenv
from utils.llm_client import CustomLLMClient

load_dotenv()


def test_json_extraction():
    """Test JSON extraction from DeepSeek R1 reasoning output."""
    print("="*60)
    print("Testing JSON Extraction from Reasoning Model")
    print("="*60)

    try:
        print("\nInitializing CustomLLMClient...")
        client = CustomLLMClient()

        print(f"Model: {client.model_name}")
        print(f"Base URL: {os.getenv('CUSTOM_LLM_BASE_URL')}")

        # Test with a structured JSON request
        system_prompt = """You are a helpful assistant that returns JSON responses."""

        user_prompt = """Please respond with ONLY valid JSON (no markdown, no code blocks):

{
  "score": 85,
  "analysis": "This is a test analysis",
  "suggestions": [
    {
      "category": "Skills",
      "text": "Add Python",
      "suggested_text": "Add skill: Python"
    }
  ]
}"""

        print("\nSending JSON test request...")
        print(f"Prompt: {user_prompt[:100]}...")

        response = client.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )

        print("\n" + "="*60)
        print("RAW RESPONSE:")
        print("="*60)
        print(response[:1000])
        print("...")
        print("="*60)

        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(response)
            print("\n[SUCCESS] JSON parsed successfully!")
            print(f"Score: {parsed.get('score')}")
            print(f"Analysis: {parsed.get('analysis')}")
            print(f"Suggestions: {len(parsed.get('suggestions', []))}")
            return True
        except json.JSONDecodeError as e:
            print(f"\n[FAILED] JSON parsing failed: {e}")
            print(f"Response starts with: {response[:100]}")
            return False

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_json_extraction()
    exit(0 if success else 1)
