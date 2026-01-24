# Formatting Rules - Agent Responsibilities

## Core Principle

**USER'S FORMATTING IS SACRED. NO AGENT MAY AUTOMATICALLY CHANGE FORMATTING.**

All formatting changes must be:
1. Proposed/suggested by Agent 4
2. Reviewed by user
3. Approved by user
4. Only then implemented

---

## Agent Roles

### Agent 1: Scorer & Analyzer
**Scope:** Content suggestions only
- ✅ CAN suggest content improvements (add skills, quantify achievements, etc.)
- ❌ CANNOT suggest formatting changes
- ❌ CANNOT modify formatting

**Why:** Agent 1's job is to analyze content match with job description, not visual formatting.

---

### Agent 2: Resume Modifier
**Scope:** Apply approved content changes ONLY
- ✅ CAN apply user-approved content suggestions
- ❌ CANNOT change ANY formatting
- ❌ CANNOT touch bold, italic, colors, fonts, HTML/CSS

**Explicit Prohibitions:**
```
❌ ABSOLUTELY FORBIDDEN - DO NOT TOUCH FORMATTING:
- NEVER change bold formatting (** or <b> tags)
- NEVER change italic formatting (* or <i> tags)
- NEVER change colors (HTML color tags or CSS)
- NEVER change font sizes, styles, or any visual formatting
- NEVER remove user's custom HTML/CSS formatting
- PRESERVE ALL existing formatting EXACTLY as it appears in the original
```

**Why:** Agent 2 modifies content based on user selections. Formatting is handled separately.

---

### Agent 3: Re-scorer
**Scope:** Score content quality
- ✅ CAN evaluate content match
- ❌ CANNOT suggest formatting changes
- ❌ CANNOT modify formatting

**Why:** Agent 3 evaluates content improvements, not visual presentation.

---

### Agent 4: Formatting Validator
**Scope:** Propose formatting improvements ONLY
- ✅ CAN report formatting issues (inconsistent dates, mixed bullet styles, etc.)
- ✅ CAN suggest formatting improvements
- ✅ CAN recommend changes to visual presentation
- ❌ CANNOT automatically implement ANY changes
- ❌ CANNOT modify the resume in ANY way

**Current Behavior:**
- Reports issues: CRITICAL, WARNING, INFO
- Provides recommendations
- User reviews and decides whether to implement
- **Implementation would require user approval + new agent or manual edit**

**Example Output:**
```
ISSUES:
- [WARNING] [Date Format] Inconsistent date formats: some use "Jan 2020", others use "2020-01"
- [INFO] [Bullet Style] Mixed bullet point styles (-, •, *)

RECOMMENDATIONS:
- Standardize all dates to "Mon YYYY - Mon YYYY" format
- Use consistent bullet style throughout (recommend -)
```

**Why:** Agent 4 is the ONLY agent that understands formatting, but it only REPORTS, never AUTO-APPLIES.

---

### Agent 5: Resume Optimizer
**Scope:** Apply approved content optimizations ONLY
- ✅ CAN remove approved bullet points
- ✅ CAN condense approved text
- ❌ CANNOT change ANY formatting
- ❌ CANNOT touch bold, italic, colors, fonts, HTML/CSS

**Explicit Prohibitions:**
```
❌ ABSOLUTELY FORBIDDEN - DO NOT TOUCH FORMATTING:
- NEVER change bold formatting (** or <b> tags)
- NEVER change italic formatting (* or <i> tags)
- NEVER change colors (HTML color tags or CSS)
- NEVER change font sizes, styles, or any visual formatting
- NEVER remove user's custom HTML/CSS formatting
- PRESERVE ALL existing formatting EXACTLY as it appears in the original
```

**Why:** Agent 5 optimizes content length, not visual formatting.

---

### Agent 6: Freeform Editor
**Scope:** Apply user-requested changes
- ✅ CAN modify content when user explicitly requests
- ✅ CAN modify formatting when user explicitly requests
- ⚠️ ONLY acts on explicit user instructions

**Why:** Freeform editor directly implements whatever the user asks for.

---

### Agent 7: Cover Letter Writer
**Scope:** Generate cover letter
- ✅ CAN read resume for context
- ❌ CANNOT modify resume
- ❌ CANNOT touch resume formatting

**Why:** Agent 7 creates a separate document (cover letter), doesn't touch the resume.

---

## Formatting Change Workflow

### Current State (After This Fix)

```
User has resume with bold blue company names
         ↓
Agent 2 modifies content (adds skills, updates summary)
         ↓
✅ Bold blue formatting PRESERVED
         ↓
Agent 5 optimizes (removes bullets)
         ↓
✅ Bold blue formatting PRESERVED
         ↓
Agent 4 validates and reports:
  "WARNING: Company names use custom HTML color.
   This may not display correctly in all ATS systems.
   RECOMMENDATION: Consider using standard markdown formatting."
         ↓
User sees recommendation, decides:
  - Option A: Ignore (keep bold blue companies) ✅
  - Option B: Approve & use Agent 6 freeform to change
         ↓
No automatic changes to formatting ✅
```

---

## Protected Formatting Elements

ALL of these MUST be preserved by Agents 2 and 5:

1. **Bold text**: `**text**` or `<b>text</b>`
2. **Italic text**: `*text*` or `<i>text</i>`
3. **Colors**: `<span style="color: #1a73e8;">text</span>`
4. **Font sizes**: `<span style="font-size: 14px;">text</span>`
5. **Custom HTML/CSS**: Any HTML tags or CSS styles
6. **Links**: `[text](url)`
7. **Headers**: `#`, `##`, `###`
8. **Line breaks**: `\n`, `<br>`
9. **Any other visual formatting**

---

## Implementation Details

### Agent 2 Prompt (lines 79-87)
```
❌ ABSOLUTELY FORBIDDEN - DO NOT TOUCH FORMATTING:
- NEVER change bold formatting (** or <b> tags)
- NEVER change italic formatting (* or <i> tags)
- NEVER change colors (HTML color tags or CSS)
- NEVER change font sizes, styles, or any visual formatting
- NEVER remove user's custom HTML/CSS formatting
- PRESERVE ALL existing formatting EXACTLY as it appears in the original
- Your ONLY job is to modify CONTENT based on approved suggestions
- Formatting changes are STRICTLY FORBIDDEN and handled by a different agent
```

### Agent 5 Prompt (lines 304-312)
```
❌ ABSOLUTELY FORBIDDEN - DO NOT TOUCH FORMATTING:
- NEVER change bold formatting (** or <b> tags)
- NEVER change italic formatting (* or <i> tags)
- NEVER change colors (HTML color tags or CSS)
- NEVER change font sizes, styles, or any visual formatting
- NEVER remove user's custom HTML/CSS formatting
- PRESERVE ALL existing formatting EXACTLY as it appears in the original
- Your ONLY job is to apply content optimizations (remove bullets, condense text)
- Formatting changes are STRICTLY FORBIDDEN and handled by a different agent
```

---

## Summary

| Agent | Can Propose Formatting? | Can Auto-Apply Formatting? | Notes |
|-------|------------------------|---------------------------|-------|
| Agent 1 | ❌ No | ❌ No | Content suggestions only |
| Agent 2 | ❌ No | ❌ No | Applies content changes, preserves formatting |
| Agent 3 | ❌ No | ❌ No | Scores content only |
| Agent 4 | ✅ YES | ❌ NO | Reports issues, makes recommendations |
| Agent 5 | ❌ No | ❌ No | Optimizes content, preserves formatting |
| Agent 6 | ✅ Yes (user-requested) | ✅ Yes (user-requested) | Freeform editor |
| Agent 7 | N/A | N/A | Doesn't touch resume |

**KEY TAKEAWAY:** Only Agent 4 can PROPOSE formatting changes. NO agent can AUTO-APPLY them. User must explicitly approve and implement via Agent 6 or manual editing.
