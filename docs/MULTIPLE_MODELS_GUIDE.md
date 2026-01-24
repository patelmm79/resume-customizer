# Multiple Models Configuration Guide

This guide explains how to configure multiple models per LLM provider in the Resume Customizer application.

## Overview

By default, the application provides a curated list of models for each provider:
- **Gemini**: 3 models (2.0-flash-exp, 1.5-pro, 1.5-flash)
- **Claude**: 3 models (3.5-sonnet, 3.5-haiku, 3-opus)
- **Custom**: 1 model (configurable)

You can customize these lists to include additional models or restrict to specific models you want to use.

## Configuration

Add the following environment variables to your `.env` file to customize available models:

### Gemini Models

```bash
# Comma-separated list of Gemini models
GEMINI_MODELS=gemini-2.0-flash-exp,gemini-1.5-pro,gemini-1.5-flash,gemini-2.0-flash-thinking-exp
```

**Use cases:**
- Add experimental models (e.g., thinking-exp)
- Restrict to only fast models for cost savings
- Test different model versions

### Claude Models

```bash
# Comma-separated list of Claude models
CLAUDE_MODELS=claude-3-5-sonnet-20241022,claude-3-5-haiku-20241022,claude-3-opus-20240229
```

**Use cases:**
- Only show Haiku for fast, cost-effective processing
- Include multiple Sonnet versions for testing
- Add new Claude models as they're released

### Custom/Local Models

```bash
# Comma-separated list of custom models
CUSTOM_MODELS=llama3:70b,mixtral:8x7b,qwen2.5:14b,gemma2:27b
```

**Use cases:**
- Multiple Ollama models installed locally
- Multiple LM Studio models loaded
- Multiple OpenAI model tiers (gpt-4, gpt-3.5-turbo)
- Different Azure OpenAI deployments

## Examples

### Example 1: Ollama with Multiple Local Models

```bash
# .env file
CUSTOM_LLM_API_KEY=ollama
CUSTOM_LLM_BASE_URL=http://localhost:11434/v1
CUSTOM_LLM_MODEL=llama3:70b

# Add multiple Ollama models to dropdown
CUSTOM_MODELS=llama3:70b,llama3:8b,mixtral:8x7b,qwen2.5:14b,gemma2:27b
```

**Result:** The UI dropdown will show all 5 models, and you can switch between them without restarting the app.

### Example 2: LM Studio with Multiple Models

```bash
# .env file
CUSTOM_LLM_API_KEY=lm-studio
CUSTOM_LLM_BASE_URL=http://localhost:1234/v1
CUSTOM_LLM_MODEL=llama-3.1-8b

# Add multiple LM Studio models
CUSTOM_MODELS=llama-3.1-8b,mistral-7b,qwen2.5-14b,phi-3-mini
```

**Note:** Ensure the models are downloaded in LM Studio before selecting them in the dropdown.

### Example 3: OpenAI with Multiple Tiers

```bash
# .env file
CUSTOM_LLM_API_KEY=sk-your-openai-key-here
CUSTOM_LLM_BASE_URL=https://api.openai.com/v1
CUSTOM_LLM_MODEL=gpt-4-turbo-preview

# Add multiple OpenAI models
CUSTOM_MODELS=gpt-4-turbo-preview,gpt-4,gpt-3.5-turbo,gpt-3.5-turbo-16k
```

**Result:** You can switch between GPT-4 and GPT-3.5 models based on your needs (quality vs. cost).

### Example 4: Gemini - Testing Experimental Models

```bash
# .env file
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp

# Add experimental thinking model
GEMINI_MODELS=gemini-2.0-flash-exp,gemini-2.0-flash-thinking-exp,gemini-1.5-pro
```

**Use case:** Test new experimental models while keeping production-ready models available.

### Example 5: Claude - Cost Optimization

```bash
# .env file
ANTHROPIC_API_KEY=your-anthropic-key-here
CLAUDE_MODEL=claude-3-5-haiku-20241022

# Only show Haiku model (most cost-effective)
CLAUDE_MODELS=claude-3-5-haiku-20241022
```

**Use case:** Restrict to only cost-effective models for high-volume processing.

## How It Works

1. **Default Behavior**: If you don't set `*_MODELS` environment variables, the application uses built-in defaults.

2. **Custom Lists**: When you set `GEMINI_MODELS`, `CLAUDE_MODELS`, or `CUSTOM_MODELS`, the application uses your custom list instead of defaults.

3. **Dynamic Loading**: The model list is loaded when the app starts, so you need to restart Streamlit after changing `.env` to see new models.

4. **Model Selection**: The selected model is passed to the LLM client and used for all agent operations.

## Benefits

✅ **Flexibility**: Test different model versions without code changes

✅ **Cost Control**: Restrict to cost-effective models

✅ **Local Development**: Easily switch between multiple local models

✅ **Multi-Provider**: Different model lists per provider

✅ **Easy Updates**: Add new models as they're released

## Troubleshooting

### Models not appearing in dropdown

**Issue**: You added models to `.env` but they don't show up.

**Solution**: Restart the Streamlit app:
```bash
# Stop the app (Ctrl+C)
streamlit run app.py
```

### Model not found error

**Issue**: Selected model returns "model not found" error.

**Solutions:**
- **Ollama**: Ensure model is downloaded (`ollama pull llama3:70b`)
- **LM Studio**: Ensure model is loaded in LM Studio
- **OpenAI**: Check that model name matches exactly (case-sensitive)
- **Gemini/Claude**: Verify model is available in your API tier

### Empty model list

**Issue**: Dropdown shows no models.

**Solutions:**
- Check for typos in `*_MODELS` environment variables
- Ensure comma-separated format (no spaces around commas is okay)
- Check that at least one model is specified

## Best Practices

1. **Keep a default model**: Always specify a default model in `*_MODEL` env var that you know works.

2. **Test models**: Before adding a model to production, test it individually to ensure it works with your API key.

3. **Document your choices**: Comment your `.env` file to explain why you chose specific models.

4. **Version control**: Add `.env.example` with your model configuration structure for team members.

5. **Monitor costs**: Different models have different pricing - be mindful when switching between them.

## Summary

The multiple models feature gives you complete control over which LLM models are available in your Resume Customizer application. Simply set the `*_MODELS` environment variables in your `.env` file with comma-separated model names, and they'll appear in the UI dropdown.

This is especially useful for:
- Local LLM users running multiple Ollama/LM Studio models
- Cost-conscious users wanting to restrict model options
- Developers testing different model versions
- Teams with specific model requirements
