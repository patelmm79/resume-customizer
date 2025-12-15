# Model Selection Quick Reference

## TL;DR - Which Model Should I Use?

**For resume analysis and structured output tasks (this app):**

✅ **Recommended**: `gemini-2.0-flash-exp` (fast, reliable, works great)
✅ **Alternative**: `claude-sonnet-4-5` (highest quality, slightly slower)
✅ **Budget**: `gpt-4o-mini` (good balance of speed and cost)

❌ **Avoid**: Any model with "R1" or "reasoning" in the name (they don't follow JSON formatting)

---

## Detailed Model Comparison

### Google Gemini Models

| Model | JSON Quality | Speed | Cost | Best For |
|-------|--------------|-------|------|----------|
| **gemini-2.0-flash-exp** | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ Fast | 💰 Low | **Default choice** - resume analysis |
| gemini-1.5-pro | ⭐⭐⭐⭐⭐ | ⚡⚡ Medium | 💰💰 Medium | Complex analysis, high accuracy needed |
| gemini-1.5-flash | ⭐⭐⭐⭐ | ⚡⚡⚡ Fast | 💰 Low | High-volume processing |

**Configuration** (in `.env`):
```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_MODELS=gemini-2.0-flash-exp,gemini-1.5-pro,gemini-1.5-flash
```

### Anthropic Claude Models

| Model | JSON Quality | Speed | Cost | Best For |
|-------|--------------|-------|------|----------|
| **claude-sonnet-4-5** | ⭐⭐⭐⭐⭐ | ⚡⚡ Medium | 💰💰 Medium | **Highest quality** - mission-critical tasks |
| claude-haiku-4-5 | ⭐⭐⭐⭐ | ⚡⚡⚡ Fast | 💰 Low | Fast processing, good quality |
| claude-opus-4-1 | ⭐⭐⭐⭐⭐ | ⚡ Slow | 💰💰💰 High | Most capable, complex reasoning |

**Configuration** (in `.env`):
```bash
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODELS=claude-sonnet-4-5,claude-haiku-4-5,claude-opus-4-1
```

### OpenAI Models (via Custom endpoint)

| Model | JSON Quality | Speed | Cost | Best For |
|-------|--------------|-------|------|----------|
| **gpt-4o** | ⭐⭐⭐⭐⭐ | ⚡⚡ Medium | 💰💰 Medium | Excellent all-around |
| **gpt-4o-mini** | ⭐⭐⭐⭐ | ⚡⚡⚡ Fast | 💰 Low | Production at scale |
| gpt-4-turbo | ⭐⭐⭐⭐⭐ | ⚡ Slow | 💰💰💰 High | Complex tasks |

**Configuration** (in `.env`):
```bash
CUSTOM_LLM_API_KEY=your_openai_key
CUSTOM_LLM_BASE_URL=https://api.openai.com/v1
CUSTOM_LLM_MODEL=gpt-4o-mini
CUSTOM_MODELS=gpt-4o,gpt-4o-mini,gpt-4-turbo
```

### DeepSeek Models

| Model | JSON Quality | Speed | Cost | Best For |
|-------|--------------|-------|------|----------|
| DeepSeek-V3 | ⭐⭐⭐⭐ | ⚡⚡ Medium | 💰 Low | Cost-effective alternative |
| DeepSeek-R1-* | ❌ **NOT COMPATIBLE** | ⚡⚡ Medium | 💰 Low | ❌ Do not use for this app |

**Why R1 doesn't work**: DeepSeek R1 models are "reasoning models" that output their thinking process in plain text instead of following JSON format instructions.

**If using DeepSeek** (in `.env`):
```bash
CUSTOM_LLM_API_KEY=your_key
CUSTOM_LLM_BASE_URL=your_deepseek_endpoint
CUSTOM_LLM_MODEL=deepseek-chat  # Use base model, NOT R1
```

---

## Quick Setup Guide

### Step 1: Choose Your Provider

Pick based on your priorities:

- **Fast & Free tier available** → Gemini (`gemini-2.0-flash-exp`)
- **Highest quality output** → Claude (`claude-sonnet-4-5`)
- **Best ecosystem integration** → OpenAI (`gpt-4o-mini`)
- **Most cost-effective** → Gemini Flash or GPT-4o Mini

### Step 2: Configure `.env`

Copy `.env.example` to `.env` and add your API key:

```bash
# For Gemini (recommended)
GEMINI_API_KEY=AIza...your_key_here

# For Claude
ANTHROPIC_API_KEY=sk-ant-...your_key_here

# For OpenAI
CUSTOM_LLM_API_KEY=sk-...your_key_here
CUSTOM_LLM_BASE_URL=https://api.openai.com/v1
CUSTOM_LLM_MODEL=gpt-4o-mini
```

### Step 3: Select in UI

1. Start the app: `streamlit run app.py`
2. Open the sidebar (top-left)
3. Choose your provider from the dropdown
4. Select the specific model
5. Start analyzing resumes!

---

## Troubleshooting

### ❌ "Failed to parse response. Please try again."

**Cause**: You're using a reasoning model (R1, o1) or incompatible model.

**Solution**:
1. Open sidebar
2. Switch provider to "Gemini" or "Claude"
3. Select a recommended model from the list above
4. Try again

### ❌ "No LLM provider configured"

**Cause**: No provider selected or missing API key.

**Solution**:
1. Check `.env` file has valid API key for your chosen provider
2. Restart Streamlit: `Ctrl+C` then `streamlit run app.py`
3. Select provider in sidebar

### ❌ "API key invalid" or authentication errors

**Solution**:
1. Verify API key is correct in `.env`
2. Check API key hasn't expired
3. Ensure sufficient credits/quota
4. Try a different provider temporarily

---

## Cost Estimates

**For a typical resume analysis** (~2000 tokens input, ~1500 tokens output):

| Model | Cost per Analysis | Cost per 1000 Analyses |
|-------|-------------------|------------------------|
| gemini-2.0-flash-exp | ~$0.001 | ~$1 |
| gpt-4o-mini | ~$0.002 | ~$2 |
| claude-haiku-4-5 | ~$0.003 | ~$3 |
| claude-sonnet-4-5 | ~$0.015 | ~$15 |
| gpt-4o | ~$0.020 | ~$20 |

*Prices approximate and subject to change. Check provider websites for current pricing.*

---

## API Key Links

- **Gemini**: https://makersuite.google.com/app/apikey
- **Claude**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/api-keys
- **DeepSeek**: https://platform.deepseek.com/

---

## Need Help?

1. Check `LESSONS_LEARNED.md` for detailed technical information
2. Review `CLAUDE.md` for architecture overview
3. Open an issue on GitHub
4. Check provider documentation (links above)

**Last Updated**: December 7, 2025
