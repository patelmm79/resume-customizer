# Coding Standards for Resume Customizer

## Core Principle: NO REGEX PARSING FOR LLM RESPONSES

**ALL agent LLM responses MUST be parsed using JSON, never regex.**

---

## LLM Response Parsing

### ✅ CORRECT: JSON Parsing

All agents that receive structured data from LLMs must:

1. **Request JSON format explicitly in prompts**
   ```python
   user_prompt = f"""...

   Please provide your response in VALID JSON format ONLY (no markdown, no code blocks, just pure JSON):

   {{
     "field1": "value1",
     "field2": ["item1", "item2"]
   }}

   CRITICAL:
   - Return ONLY valid JSON, no markdown formatting, no ```json code blocks
   """
   ```

2. **Use double curly braces in f-strings**
   - In Python f-strings, use `{{` and `}}` to represent literal `{` and `}` in JSON examples
   - This prevents format string errors

3. **Parse with json.loads()**
   ```python
   import json

   def _parse_response(self, response: str) -> Dict:
       # Clean up response - remove markdown code blocks
       cleaned = response.strip()

       if cleaned.startswith("```"):
           first_newline = cleaned.find('\n')
           if first_newline != -1:
               cleaned = cleaned[first_newline + 1:]
           if cleaned.endswith("```"):
               cleaned = cleaned[:-3].strip()

       try:
           parsed = json.loads(cleaned)
           # Extract and structure data...
           return structured_result

       except json.JSONDecodeError as e:
           # Fallback: Extract JSON from text
           json_match = re.search(r'\{[\s\S]*\}', cleaned)
           if json_match:
               try:
                   parsed = json.loads(json_match.group(0))
                   # ...
               except json.JSONDecodeError:
                   pass

           # Return error result
           return {
               "error": "Failed to parse response",
               "data": []
           }
   ```

4. **Include fallback parsing**
   - Sometimes LLMs wrap JSON in text
   - Use regex `r'\{[\s\S]*\}'` to extract JSON object
   - Still parse with `json.loads()`, not regex

### ❌ INCORRECT: Regex Parsing

**NEVER** parse LLM responses using regex patterns like:
- `re.search(r'SCORE:\s*(\d+)', response)`
- `re.search(r'\[CATEGORY:\s*([^\]]+)\]', text)`
- Line-by-line parsing with string operations
- Section detection with `startswith()` checks

**Why?**
- LLMs use inconsistent formatting (headers, bold, bullets)
- Regex becomes fragile with 100+ lines of pattern matching
- Fails silently when LLM uses unexpected format
- Difficult to debug and maintain

---

## Agent Implementation Standards

### Agent Structure

```python
class SomeAgent:
    def __init__(self, debug_mode: bool = False):
        self.client = get_agent_llm_client()
        self.debug_mode = debug_mode

    def process(self, input_data: str) -> Dict:
        """Main processing method."""
        system_prompt = """..."""

        user_prompt = f"""...

        Please provide your response in VALID JSON format ONLY:
        {{
          "field": "value"
        }}
        """

        response = self.client.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4
        )

        if self.debug_mode:
            print(f"[AgentX DEBUG] Response length: {len(response)} chars")

        return self._parse_response(response)

    def _parse_response(self, response: str) -> Dict:
        """Parse JSON response."""
        import json

        cleaned = response.strip()

        # Remove markdown code blocks
        if cleaned.startswith("```"):
            # ...cleanup logic...
            pass

        if self.debug_mode:
            print(f"[AgentX DEBUG] Cleaned: {cleaned[:500]}")

        try:
            parsed = json.loads(cleaned)

            if self.debug_mode:
                print(f"[AgentX DEBUG] JSON parsed successfully")

            return self._structure_result(parsed)

        except json.JSONDecodeError as e:
            if self.debug_mode:
                print(f"[AgentX DEBUG] JSON parse failed: {str(e)}")

            # Fallback logic...
            return {"error": "Parse failed"}
```

### Debug Mode

All agents must support debug mode:

1. **Accept debug_mode parameter**
   ```python
   def __init__(self, debug_mode: bool = False):
       self.debug_mode = debug_mode
   ```

2. **Print debug info conditionally**
   ```python
   if self.debug_mode:
       print(f"[Agent5 DEBUG] Response length: {len(response)} chars")
       print(f"[Agent5 DEBUG] Parsed {len(suggestions)} suggestions")
   ```

3. **Check environment variable in workflow nodes**
   ```python
   import os
   debug_mode = os.getenv('DEBUG_MODE', '0') == '1'
   agent = SomeAgent(debug_mode=debug_mode)
   ```

---

## Prompt Engineering Standards

### JSON Request Format

Always include these elements in prompts:

1. **Clear JSON structure example** (with escaped braces in f-strings)
2. **"CRITICAL:" section** with formatting rules
3. **Explicit instruction**: "Return ONLY valid JSON, no markdown formatting, no ```json code blocks"

### Example:

```python
user_prompt = f"""Analyze this data:

DATA:
{data}

Please provide your response in VALID JSON format ONLY (no markdown, no code blocks, just pure JSON):

{{
  "score": 85,
  "analysis": "Your analysis here",
  "items": [
    {{
      "category": "CategoryName",
      "description": "Description text"
    }}
  ]
}}

CRITICAL:
- Return ONLY valid JSON, no markdown formatting, no ```json code blocks
- Each item must have category and description fields
- Be specific and actionable
"""
```

---

## Anti-Patterns to Avoid

### ❌ Don't: Regex Line Parsing

```python
# BAD
for line in response.split('\n'):
    if line.startswith("SCORE:"):
        score = int(line.replace("SCORE:", "").strip())
    elif line.startswith("-"):
        # Parse suggestion...
```

### ❌ Don't: Multiple Format Support

```python
# BAD - trying to handle too many formats
if "[CATEGORY:" in text:
    # ...
elif "**CATEGORY:**" in text:
    # ...
elif "**CATEGORY:" in text:
    # ...
elif "CATEGORY:" in text:
    # ...
```

### ❌ Don't: Silent Failures

```python
# BAD
try:
    suggestions = parse_suggestions(response)
except:
    suggestions = []  # Silently returns empty
```

### ✅ Do: JSON with Error Handling

```python
# GOOD
try:
    parsed = json.loads(cleaned_response)
    suggestions = self._structure_suggestions(parsed)

    if self.debug_mode:
        print(f"[Agent DEBUG] Successfully parsed {len(suggestions)} items")

    return suggestions

except json.JSONDecodeError as e:
    if self.debug_mode:
        print(f"[Agent DEBUG] JSON parse failed: {str(e)}")
        print(f"[Agent DEBUG] Response: {cleaned_response[:500]}")

    return {
        "error": f"Failed to parse response: {str(e)}",
        "suggestions": []
    }
```

---

## Testing Standards

### Manual Testing

1. **Enable debug mode** in Streamlit UI
2. **Check terminal output** for parsing success
3. **Look for**: `[Agent DEBUG] JSON parsed successfully: N items`
4. **If parsing fails**, check for format mismatches

### Expected Debug Output

```
[Agent5 DEBUG] Response length: 5880 chars
[Agent5 DEBUG] Cleaned response first 500 chars:
{
  "analysis": "...",
  "suggestions": [...]
}

[Agent5 DEBUG] JSON parsed successfully: 8 suggestions
```

---

## Migration Guide

### Converting Regex Parser to JSON

1. **Update prompt** to request JSON format with escaped braces
2. **Replace `_parse_response()` method** with JSON parser
3. **Add debug output** for parsing status
4. **Test** with debug mode enabled
5. **Remove** old regex parsing code
6. **Validate** syntax with `python -m py_compile`

### Example Migration

**Before:**
```python
if line.startswith("SUGGESTIONS:"):
    current_section = "suggestions"
elif current_section == "suggestions" and line.startswith("-"):
    # Complex regex extraction...
```

**After:**
```python
parsed = json.loads(cleaned_response)
suggestions = parsed.get("suggestions", [])
```

---

## Summary

### Golden Rules

1. ✅ **ALL LLM response parsing MUST use JSON**
2. ✅ **Use `{{` `}}` in f-string JSON examples**
3. ✅ **Include fallback JSON extraction**
4. ✅ **Support debug mode in all agents**
5. ✅ **Print clear debug messages**
6. ❌ **NEVER use regex for structured data parsing**
7. ❌ **NEVER parse line-by-line with string operations**
8. ❌ **NEVER support multiple format variations**

### Benefits

- **Reliability**: JSON is unambiguous
- **Maintainability**: Simple parsing code
- **Debuggability**: Clear error messages
- **Extensibility**: Easy to add fields

---

## References

- See `agents/agent_1_scorer.py` for Agent 1 JSON parser implementation
- See `agents/agent_5_optimizer.py` for Agent 5 JSON parser implementation
- See `JSON_PARSER_UPDATE.md` for migration details
