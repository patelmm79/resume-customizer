"""Test vLLM server limits by requesting increasing max_tokens."""
import os
from dotenv import load_dotenv
from openai import OpenAI
import httpx

load_dotenv()

api_key = os.getenv("CUSTOM_LLM_API_KEY")
base_url = os.getenv("CUSTOM_LLM_BASE_URL")
model = os.getenv("CUSTOM_LLM_MODEL")

def add_api_key_header(request: httpx.Request):
    if "Authorization" in request.headers:
        del request.headers["Authorization"]
    request.headers["X-API-Key"] = api_key

http_client = httpx.Client(
    event_hooks={"request": [add_api_key_header]},
    timeout=120.0
)

client = OpenAI(
    api_key="dummy",
    base_url=base_url,
    http_client=http_client
)

print(f"Testing vLLM server: {base_url}")
print(f"Model: {model}")
print("=" * 80)

# Test with different max_tokens values
test_values = [256, 512, 1024, 2048, 4096]

for max_tokens_request in test_values:
    print(f"\n[TEST] Requesting max_tokens={max_tokens_request}")
    print("-" * 80)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes long, detailed responses."},
                {"role": "user", "content": f"Write a very detailed analysis that is at least {max_tokens_request * 3} characters long. Keep writing until you reach that length. Include multiple paragraphs and details."}
            ],
            max_tokens=max_tokens_request,
            temperature=0.7
        )

        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        usage = response.usage

        print(f"✓ Requested: {max_tokens_request} tokens")
        print(f"  finish_reason: {finish_reason}")
        print(f"  Response length: {len(content)} chars (~{len(content)//4} tokens)")
        if usage:
            print(f"  Actual tokens used: {usage.completion_tokens}")
        print(f"  First 100 chars: {content[:100]}")

        # Check if we got less than requested
        actual_tokens = len(content) // 4
        if actual_tokens < (max_tokens_request * 0.5):
            print(f"  ⚠️  WARNING: Got {actual_tokens} tokens but requested {max_tokens_request}")
            print(f"  ⚠️  Server may have a lower limit configured!")

    except Exception as e:
        print(f"✗ ERROR: {e}")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("If responses are consistently around the same size regardless of max_tokens,")
print("the vLLM server has a hard limit configured via --max-model-len or similar.")
