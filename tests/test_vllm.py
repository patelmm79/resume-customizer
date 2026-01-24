"""Test vLLM endpoint with retries."""
import os
import time
from dotenv import load_dotenv
from utils.llm_client import CustomLLMClient

load_dotenv()

def test_vllm_with_retries(max_retries=3, delay=5):
    """Test vLLM endpoint with retries."""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n{'='*60}")
            print(f"Attempt {attempt}/{max_retries}")
            print(f"{'='*60}")

            print("Initializing CustomLLMClient...")
            client = CustomLLMClient()

            print(f"Model: {client.model_name}")
            print(f"Base URL: {os.getenv('CUSTOM_LLM_BASE_URL')}")
            print(f"API Key: {os.getenv('CUSTOM_LLM_API_KEY')[:20]}...")

            print("\nSending test request...")
            response = client.generate_with_system_prompt(
                system_prompt="You are a helpful assistant. Respond concisely.",
                user_prompt="Say 'Hello!' in one word.",
                temperature=0.7
            )

            print(f"\nResponse: {response}")
            print("\nSUCCESS: vLLM endpoint is working!")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"\nERROR: {error_msg}")

            if "403" in error_msg or "Forbidden" in error_msg:
                print("\n403 Forbidden - Check:")
                print("  1. API key is valid and matches Secret Manager")
                print("  2. API key has not expired")
                print("  3. Cloud Run service allows this key")

            elif "Service Unavailable" in error_msg or "503" in error_msg:
                print("\n503 Service Unavailable - Container might be:")
                print("  1. Still starting up (wait 30-60 seconds)")
                print("  2. Overloaded or out of memory")
                print("  3. Crashed (check Cloud Run logs)")

            elif "404" in error_msg or "Not Found" in error_msg:
                print("\n404 Not Found - Check:")
                print("  1. Base URL is correct")
                print("  2. Endpoint path includes /v1")

            elif "Connection" in error_msg or "timeout" in error_msg.lower():
                print("\nConnection issue - Container might be:")
                print("  1. Not running (check Cloud Run console)")
                print("  2. Network issues")

            if attempt < max_retries:
                print(f"\nWaiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                print(f"\nFailed after {max_retries} attempts.")
                return False

    return False

if __name__ == "__main__":
    print("Testing vLLM endpoint...")
    print(f"Endpoint: {os.getenv('CUSTOM_LLM_BASE_URL')}")

    success = test_vllm_with_retries(max_retries=3, delay=10)
    exit(0 if success else 1)
