"""Centralized resume standards and guidelines for all agents."""

# Resume structure and formatting standards
RESUME_STANDARDS = """
## Resume Structure Standards

### Header Format
- Candidate name in bold at top
- Contact information: email, phone, LinkedIn (optional)
- Brief headline (max 10 words) describing the candidate

### Section Order
1. Summary (optional but recommended)
2. Skills
3. Experience (most important section)
4. Education
5. Certifications (if applicable)

### Experience Section Rules
**CRITICAL - JOB METADATA FORMAT:**
- Format: **Job Title** | Company Name | Location | *Employment Type*\\
- MUST end with backslash (\\) for proper formatting
- Example: **Senior Data Scientist** | Google | New York, NY | *Full-time*\\

**CRITICAL - JOB HEADLINE:**
- Immediately follows metadata line (no blank lines)
- Format: *Brief one-line description of role impact*
- Must be italicized
- Example: *Led ML infrastructure team building recommendation systems serving 100M+ users*

**CRITICAL - BULLET POINTS:**
- Use consistent bullet format throughout
- Each bullet should have a strong action verb
- Include quantifiable metrics whenever possible
- Focus on impact and results, not just responsibilities
- NO blank lines between metadata and headline
- Blank line AFTER headline, before bullets

**Example Structure:**
```
**Senior Data Scientist** | Google | New York, NY | *Full-time*\\
*Led ML infrastructure team building recommendation systems serving 100M+ users*

- Architected and deployed real-time ML pipeline processing 1B+ events daily, reducing latency by 40%
- Managed team of 5 engineers delivering $5M in cost savings through infrastructure optimization
- Collaborated with product teams to increase user engagement by 25% through personalized recommendations
```

### Handling Old Roles
For roles other than most recent 4 roles:
- Keep bullet points only if highly relevant to target job. 
- If bullet points are kept, condense to focus on most impressive achievements
- ALWAYS Preserve job headlines even for older roles (they provide context)

### Skills Section
- Group related skills together
- Prioritize skills mentioned in job description
- Include technical skills, tools, and methodologies
- Keep concise - skills section should not dominate the resume

### Length Guidelines
- Target: 1 page (500-700 words ideal)
- Maximum: 800 words for senior roles with extensive experience
- Prioritize recent, relevant experience
- Remove or condense older/irrelevant content

### Formatting Rules
- Consistent date formats (e.g., "Jan 2020 - Present")
- Consistent use of bold, italics, and bullets
- Professional, clean markdown formatting
- No placeholder text or generic descriptions
- Proper spacing between sections
"""

# Guidelines for modification agent
MODIFICATION_GUIDELINES = """
## Modification Agent Guidelines

Your goal is to apply user-selected changes while maintaining professional formatting and structure.

### Key Principles
1. **Preserve Structure**: Maintain the resume's overall structure and formatting
2. **Apply Only Selected Changes**: Only implement suggestions that the user has checked
3. **Maintain Standards**: Follow all Resume Structure Standards above
4. **Preserve Context**: Keep the professional tone and voice consistent
5. **Quantify Impact**: When adding content, include metrics and quantifiable results

### What to Preserve
- Job headlines for all roles (especially important - they provide context)
- Existing achievements unless explicitly modifying
- Professional formatting and structure
- Contact information and header details

### What to Modify Carefully
- Summary: Enhance based on suggestions while keeping authentic voice
- Skills: Add only selected new skills; don't remove existing relevant ones
- Experience: Add/modify bullets based on suggestions; keep quantifiable metrics
- Old roles: Condense if needed, but preserve headlines and key achievements

### Critical Rules
1. ALWAYS include backslash (\\) at end of job metadata lines
2. ALWAYS include italicized job headline after metadata
3. NO blank lines between metadata and headline
4. One blank line after headline before bullets
5. Maintain consistent bullet formatting throughout
"""

# Guidelines for optimizer agent
OPTIMIZATION_GUIDELINES = """
## Optimizer Agent Guidelines

Your goal is to make the resume as concise as possible while maintaining or improving the job match score.

### Optimization Strategy
1. **Start with oldest content**: Remove or condense older, less relevant experience first
2. **Preserve recent impact**: Keep detailed descriptions for recent roles (last 3-5 years)
3. **Maintain headlines**: ALWAYS preserve job headlines - they're critical for context
4. **Reduce wordiness**: Remove redundant words, simplify phrasing
5. **Prioritize relevance**: Keep content most relevant to target job

### What to Preserve
- All job headlines (italicized descriptions under job metadata)
- Job metadata lines (with backslashes)
- Quantifiable metrics and impact statements
- Recent achievements (last 5 years)
- Skills section (keep concise but complete)

### What to Optimize
- Older roles: Reduce to 1-2 bullets highlighting most impressive achievements
- Redundant content: Remove repetitive statements
- Wordy descriptions: Simplify without losing impact
- Generic statements: Replace with specific, quantified achievements

### Optimization Order (Priority)
1. Remove truly irrelevant old roles (10+ years ago, unrelated field)
2. Condense older roles (5-10 years) to 1-2 bullets
3. Tighten wording in all bullets (remove redundancy)
4. Simplify complex sentences while preserving metrics
5. Only as last resort: condense recent roles (but keep detailed)

### Critical Rules - NEVER Remove
- Job headlines (the italicized line after metadata)
- Backslashes at end of metadata lines
- Quantifiable metrics (numbers that show impact)
- Recent achievements (last 3-5 years)
- Section structure (Summary, Skills, Experience, Education)

### Iterative Optimization
- Make changes incrementally
- Verify formatting after each change
- Ensure no critical information is lost
- Stop when further optimization would hurt score or readability
"""

# Validation criteria for both agents
VALIDATION_CRITERIA = {
    "structure": {
        "has_header": "Resume must have candidate name and contact info",
        "has_sections": "Resume must have key sections (Skills, Experience, Education)",
        "proper_order": "Sections should follow standard order"
    },
    "experience_formatting": {
        "metadata_backslash": "All job metadata lines must end with backslash (\\)",
        "has_headlines": "Each job must have italicized headline after metadata",
        "no_blank_before_headline": "No blank lines between metadata and headline",
        "blank_after_headline": "One blank line after headline before bullets"
    },
    "content_quality": {
        "has_metrics": "Experience bullets should include quantifiable metrics",
        "action_verbs": "Bullets should start with strong action verbs",
        "no_placeholders": "No generic placeholder text",
        "consistent_tense": "Consistent verb tense (past for old roles, present for current)"
    },
    "length": {
        "target_words": "500-700 words (1 page)",
        "max_words": "800 words maximum",
        "min_words": "400 words minimum"
    }
}


def get_modification_prompt_prefix() -> str:
    """Get the standards section to prepend to modification agent prompts."""
    return f"{RESUME_STANDARDS}\n\n{MODIFICATION_GUIDELINES}"


def get_optimization_prompt_prefix() -> str:
    """Get the standards section to prepend to optimizer agent prompts."""
    return f"{RESUME_STANDARDS}\n\n{OPTIMIZATION_GUIDELINES}"


def validate_resume_against_standards(resume: str) -> dict:
    """
    Validate resume against standards.

    Args:
        resume: Resume content in markdown

    Returns:
        Dictionary with validation results
    """
    issues = []

    # Check for backslashes in metadata lines
    import re
    metadata_pattern = re.compile(r'\*\*[^*]+\*\*\s*\|.*\|.*\|.*\*[^*]+\*')
    for match in metadata_pattern.finditer(resume):
        line = match.group()
        if not line.rstrip().endswith('\\'):
            issues.append({
                "severity": "CRITICAL",
                "category": "Experience Formatting",
                "description": f"Job metadata missing backslash: {line[:50]}..."
            })

    # Check for job headlines
    lines = resume.split('\n')
    for i, line in enumerate(lines):
        if metadata_pattern.match(line):
            # Check if next non-empty line is italicized
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_line = lines[j].strip()
                if not (next_line.startswith('*') and next_line.endswith('*') and not next_line.startswith('**')):
                    issues.append({
                        "severity": "WARNING",
                        "category": "Experience Formatting",
                        "description": f"Missing or improperly formatted headline after: {line[:50]}..."
                    })

    # Word count check
    word_count = len(resume.split())
    if word_count > 800:
        issues.append({
            "severity": "WARNING",
            "category": "Length",
            "description": f"Resume is {word_count} words (target: 500-700, max: 800)"
        })

    return {
        "is_valid": len([i for i in issues if i["severity"] == "CRITICAL"]) == 0,
        "issues": issues,
        "word_count": word_count
    }
