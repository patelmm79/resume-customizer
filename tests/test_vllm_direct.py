"""Direct test of vLLM server to check response length."""
import os
from dotenv import load_dotenv
import httpx
import json

load_dotenv()

# Simple test prompt
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a detailed JSON response with 'analysis' and 'suggestions' fields. Make it at least 2000 characters long. Fill with detailed analysis and multiple suggestions."}
]

api_key = os.getenv("CUSTOM_LLM_API_KEY")
base_url = os.getenv("CUSTOM_LLM_BASE_URL")
model = os.getenv("CUSTOM_LLM_MODEL")

print(f"Testing vLLM server: {base_url}")
print(f"Model: {model}")
print(f"=" * 60)

# Test 1: Direct httpx request without OpenAI SDK
print("\n[TEST 1] Direct httpx POST request")
print("=" * 60)

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

payload = {
    "model": model,
    "messages": messages,
    "max_tokens": 3000,
    "temperature": 0.7
}

with httpx.Client(timeout=120.0) as client:
    response = client.post(
        f"{base_url}/chat/completions",
        json=payload,
        headers=headers
    )

    print(f"Status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    finish_reason = data["choices"][0]["finish_reason"]

    print(f"\nfinish_reason: {finish_reason}")
    print(f"Content length: {len(content)} chars")
    print(f"Content preview (first 500 chars):\n{content[:500]}")
    print(f"\nContent end (last 200 chars):\n{content[-200:]}")

# Test 2: With OpenAI SDK
print("\n\n[TEST 2] Using OpenAI SDK")
print("=" * 60)

from openai import OpenAI

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

response = client.chat.completions.create(
    model=model,
    messages=messages,
    max_tokens=3000,
    temperature=0.7
)

content = response.choices[0].message.content
finish_reason = response.choices[0].finish_reason

print(f"finish_reason: {finish_reason}")
print(f"Content length: {len(content)} chars")
print(f"Content preview (first 500 chars):\n{content[:500]}")
print(f"\nContent end (last 200 chars):\n{content[-200:]}")

# Test 3: Check if response object has more data
print("\n\n[TEST 3] Inspecting response object")
print("=" * 60)
print(f"Response type: {type(response)}")
print(f"Response dict: {response.model_dump()}")
