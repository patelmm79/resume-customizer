# LangSmith Integration Guide

This document explains how to enable and use LangSmith tracing with the Resume Customizer application.

## Overview

LangSmith provides observability for AI applications. With LangSmith integrated, you can:
- **Trace all LLM calls** - See exactly what prompts are sent and what responses are received
- **Monitor performance** - Track latency, token usage, and error rates
- **Debug issues** - Review conversation history and identify problems
- **Analyze costs** - Monitor API usage and spending across providers
- **Compare models** - Run A/B tests between different LLM models

## Setup

### 1. Create LangSmith Account

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Sign up or log in
3. Create a new project called `resume-customizer` (or any name you prefer)

### 2. Generate API Key

1. In LangSmith, go to **Settings** → **API Keys**
2. Click **Create API Key**
3. Copy the key (you'll need it for the next step)

### 3. Configure Terraform

Update your `terraform.tfvars`:

```hcl
# Enable LangSmith tracing
langsmith_tracing = true

# Set the LangSmith endpoint
langsmith_endpoint = "https://api.smith.langchain.com"

# Set your API key (or via environment variable)
langsmith_api_key_value = "your-api-key-here"
```

**For production/CI/CD:** Never commit the API key. Instead, set it via environment variable:

```bash
export TF_VAR_langsmith_api_key_value="your-api-key"
terraform apply
```

### 4. Deploy

```bash
cd terraform
terraform apply
```

Terraform will:
- Store the API key securely in Google Cloud Secret Manager
- Configure Cloud Run with the necessary environment variables
- Enable LangSmith tracing automatically

## What Gets Traced

Once enabled, LangSmith automatically captures traces for:

### LLM Calls

**Gemini Provider:**
- Input prompt (system + user)
- Output response
- Model name
- Temperature
- Token limits
- Execution time

**Claude Provider:**
- Input prompt (system + user)
- Output response
- Model name
- Temperature
- Token limits
- Extended thinking (if enabled)
- Execution time

**Custom LLM Provider:**
- Input prompt (system + user)
- Output response
- Model name
- Temperature
- Token limits
- Retry attempts (for 503 errors)
- Structured output format (if used)
- Execution time

### Trace Tags

Each trace is tagged with:
- `llm` - Indicates it's an LLM call
- Provider name: `gemini`, `claude`, or `custom`
- Run context (agent, workflow step)

## Viewing Traces

### In LangSmith Dashboard

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Select your project (`resume-customizer`)
3. Go to **Traces** tab
4. You'll see all LLM calls with:
   - Input/output prompts
   - Latency
   - Token usage
   - Errors (if any)
   - Model used

### Filtering

Click on **Tags** to filter by:
- Provider: `gemini`, `claude`, `custom`
- Type: `llm`
- Date range
- Latency
- Errors

## Environment Variables

The application uses these environment variables (automatically set by Terraform):

```bash
LANGSMITH_TRACING=true              # Enable/disable tracing
LANGSMITH_API_KEY=your-api-key      # Secret key (from Secret Manager)
LANGSMITH_ENDPOINT=...              # API endpoint URL
LANGSMITH_PROJECT=your-gcp-project  # Project name for organizing traces
```

## Code Integration

The integration is implemented using the `@traceable` decorator from LangSmith on all LLM client methods:

**File:** `utils/llm_client.py`

```python
from langsmith import traceable

class GeminiClient(LLMClient):
    @traceable(name="gemini_generation", tags=["llm", "gemini"])
    def generate_with_system_prompt(self, ...):
        # Traces are automatically captured
        response = self.model.generate_content(...)
        return response
```

The decorator:
- Captures all inputs and outputs
- Measures execution time
- Tags traces for filtering
- Automatically sends to LangSmith if credentials are configured

## Troubleshooting

### Traces Not Appearing

1. **Check environment variables:**
   ```bash
   gcloud run services describe resume-customizer --region=us-central1 \
     --format='value(spec.template.spec.containers[0].env)'
   ```
   Verify `LANGSMITH_TRACING=true` is set

2. **Verify API key:**
   ```bash
   gcloud secrets versions access latest \
     --secret="resume_customizer-LANGSMITH_API_KEY"
   ```

3. **Check LangSmith project name:**
   - Must match the project in LangSmith dashboard
   - Default: Your GCP project name

4. **Check logs:**
   ```bash
   gcloud run logs read resume-customizer --limit 50 --region=us-central1
   ```

### High Latency in Traces

- **Network latency**: LangSmith traces are sent asynchronously, minimal impact
- **LLM provider latency**: Check individual LLM provider response times
- **Retry loops**: CustomLLM provider shows retry attempts if warming up

## Disabling Tracing

To disable LangSmith tracing:

```hcl
langsmith_tracing = false
terraform apply
```

Tracing decorator will be inactive, but the code remains instrumented for future use.

## Best Practices

1. **Use project names for organization:**
   - LANGSMITH_PROJECT is automatically set to your GCP project
   - Organize traces by environment: `dev`, `staging`, `prod`

2. **Monitor costs:**
   - Review token usage in LangSmith dashboard
   - Compare costs across providers (Gemini, Claude, etc.)

3. **Debug issues:**
   - Look at failed traces to understand error messages
   - Check retry attempts in CustomLLM traces

4. **Optimize prompts:**
   - Review successful traces to see what works
   - Identify patterns in token usage
   - Test prompt variations with A/B tracing

## Integration Details

The LangSmith integration is **minimal and non-invasive**:

- **No custom wrapper classes needed** - Uses standard `@traceable` decorator
- **Graceful degradation** - If langsmith is not installed, decorators are no-ops
- **Environment-based** - Enable/disable via configuration
- **Backward compatible** - Doesn't change any application logic
- **Secure** - API key stored in Secret Manager, never logged

See [utils/llm_client.py](utils/llm_client.py) for implementation details.

## References

- [LangSmith Documentation](https://docs.smith.langchain.com)
- [LangSmith Python SDK](https://github.com/langchain-ai/langsmith-sdk)
- [Resume Customizer Architecture](CLAUDE.md)
