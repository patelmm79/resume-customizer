# Retry Logic Implementation for vLLM Cold Start

## Problem
When using serverless vLLM deployments (Google Cloud Run, etc.), the first request after idle period can fail with:
```
Error code: 503 - {'detail': 'vLLM server unavailable: All connection attempts failed'}
```

This happens because the container needs 1-2 minutes to "warm up" (start the model, load weights, etc.).

## Solution
Implemented automatic retry logic with exponential backoff in the `CustomLLMClient` class.

## Changes Made

### 1. Updated `utils/llm_client.py`
- Added retry loop in `CustomLLMClient.generate_with_system_prompt()`
- Specifically catches 503 (Service Unavailable) errors
- Implements exponential backoff: 5s, 10s, 20s, 40s, 80s (default)
- Provides clear user feedback during retries
- After max retries, gives helpful error message

### 2. Updated `.env`
Added configurable retry settings:
```env
# Retry settings for serverless vLLM (handles cold start warm-up)
CUSTOM_LLM_MAX_RETRIES=5
CUSTOM_LLM_INITIAL_RETRY_DELAY=5.0
```

**Total wait time with defaults:** ~155 seconds (2.5 minutes)

## How It Works

When a 503 error occurs:

1. **Attempt 1 fails** → Wait 5 seconds → Retry
2. **Attempt 2 fails** → Wait 10 seconds → Retry
3. **Attempt 3 fails** → Wait 20 seconds → Retry
4. **Attempt 4 fails** → Wait 40 seconds → Retry
5. **Attempt 5 fails** → Wait 80 seconds → Retry
6. **All retries exhausted** → Show error with helpful message

The user sees clear feedback:
```
============================================================
[INFO] vLLM server is warming up (503 error)
[INFO] Attempt 1/5
[INFO] Retrying in 5.0 seconds...
============================================================
```

## Configuration

Users can customize retry behavior by editing `.env`:

### More aggressive retries (faster, more attempts):
```env
CUSTOM_LLM_MAX_RETRIES=10
CUSTOM_LLM_INITIAL_RETRY_DELAY=3.0
```

### More patient retries (longer waits):
```env
CUSTOM_LLM_MAX_RETRIES=4
CUSTOM_LLM_INITIAL_RETRY_DELAY=10.0
```

### Disable retries (fail fast):
```env
CUSTOM_LLM_MAX_RETRIES=1
CUSTOM_LLM_INITIAL_RETRY_DELAY=0.0
```

## Benefits

✅ **Automatic recovery** - No manual retry needed
✅ **User-friendly** - Clear progress messages
✅ **Configurable** - Adjust to your server's warm-up time
✅ **Smart** - Only retries 503 errors, fails fast on other errors
✅ **Exponential backoff** - Reduces server load, gives time to warm up

## Other Error Codes

The retry logic is **specific to 503 errors**. Other error codes will fail immediately:
- **401/403** - Authentication errors (fail immediately)
- **404** - Endpoint not found (fail immediately)
- **500** - Server error (fail immediately)
- **503** - Service unavailable (retry with backoff) ✅

This ensures fast failure for configuration errors while being patient with cold starts.
