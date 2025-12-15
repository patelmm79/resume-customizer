"""Test structured output with DeepSeek R1 using response_format."""
import os
from dotenv import load_dotenv
from utils.llm_client import CustomLLMClient
from agents.schemas import ResumeAnalysisSchema

load_dotenv()


def test_structured_output_deepseek_r1():
    """Test that DeepSeek R1 can produce JSON with response_format."""
    print("="*60)
    print("Testing Structured Output with DeepSeek R1")
    print("="*60)

    try:
        # Initialize client
        client = CustomLLMClient()
        print(f"\nModel: {client.model_name}")
        print(f"Base URL: {os.getenv('CUSTOM_LLM_BASE_URL')}")

        # Build response_format from schema
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "ResumeAnalysisSchema",
                "schema": ResumeAnalysisSchema.model_json_schema(),
                "strict": True,
            },
        }

        print(f"\nResponse Format Schema:")
        print(f"  Name: {response_format['json_schema']['name']}")
        print(f"  Strict: {response_format['json_schema']['strict']}")

        # Test with simple resume analysis
        system_prompt = "You are a resume analyzer. Analyze the resume and provide a score."

        user_prompt = """
Analyze this resume for a Software Engineer position:

RESUME:
John Doe
Software Engineer with 5 years experience in Python and JavaScript.

JOB DESCRIPTION:
Looking for a Software Engineer with Python, JavaScript, and cloud experience.

Provide analysis with score 1-100 and suggestions.
"""

        print("\nGenerating response with structured output...")

        response = client.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            response_format=response_format
        )

        print(f"\n{'='*60}")
        print("RAW RESPONSE:")
        print(f"{'='*60}")
        print(f"Length: {len(response)} chars")
        print(f"First 500 chars: {response[:500]}")
        print(f"{'='*60}\n")

        # Try to parse as JSON
        import json
        parsed = json.loads(response)

        print("[SUCCESS] Response is valid JSON!")
        print(f"Score: {parsed.get('score')}")
        print(f"Analysis length: {len(parsed.get('analysis', ''))}")
        print(f"Suggestions count: {len(parsed.get('suggestions', []))}")

        # Validate against Pydantic schema
        validated = ResumeAnalysisSchema(**parsed)
        print(f"\n[SUCCESS] Response matches Pydantic schema!")
        print(f"  Score type: {type(validated.score)}")
        print(f"  Score value: {validated.score}")
        print(f"  Analysis: {validated.analysis[:100]}...")

        return True

    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_structured_output_deepseek_r1()
    print("\n" + "="*60)
    if success:
        print("✓ STRUCTURED OUTPUT WORKS WITH DEEPSEEK R1!")
        print("The response_format parameter forces JSON output.")
    else:
        print("✗ Test failed - check error messages above")
    print("="*60)
    exit(0 if success else 1)
