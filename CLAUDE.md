# Resume Customizer - Agentic Application with LangGraph

## Project Overview

An intelligent resume customization system that uses multiple AI agents orchestrated by **LangGraph** to analyze, optimize, and tailor resumes to specific job descriptions.

## Architecture

This application implements a **multi-agent system with LangGraph orchestration**:

### LangGraph Workflow

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Fetch Job Desc │ (Optional - if URL provided)
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 1:       │
│  Score & Analyze│ → Score (1-100) + Suggestions
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HUMAN          │ ← User selects suggestions
│  [Checkpoint]   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 2:       │
│  Modify Resume  │ → Modified Resume
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 3:       │
│  Re-score       │ → New Score + Comparison
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 5:       │
│  Suggest Opts   │ → Optimization Suggestions
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HUMAN          │ ← User selects optimizations
│  [Checkpoint]   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 5:       │
│  Apply Opts     │ → Optimized Resume (concise)
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 4:       │
│  Validate       │ → Validation Score + Issues
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HUMAN          │ ← User reviews validation
│  [Checkpoint]   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Export PDF     │ → Professional PDF
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HUMAN          │ ← User decides to generate cover letter (optional)
│  [Checkpoint]   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 7:       │ → Cover Letter Draft
│  Write Letter   │
│  [Node]         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 8:       │ → Review Feedback
│  Review Letter  │ → Critical/Content/Minor Issues
│  [Node]         │ → Strengths
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HUMAN          │ ← User reviews feedback & adds notes
│  [Checkpoint]   │
└────────┬────────┘
         │
    ┌────┴─────┐
    ▼          ▼
[Revise]   [Approve & Export]
    │          │
    ▼          ▼
Agent 7    Cover Letter PDF
Revises
(loop back)
         │
         ▼
┌─────────────┐
│     END     │
└─────────────┘
```

### Agent 1: Resume Analyzer & Scorer
- **Input**: Original resume (markdown), job description (URL or text)
- **Output**:
  - Compatibility score (1-100)
  - Detailed analysis
  - Checkbox list of suggested changes
- **Responsibilities**:
  - Parse and understand both resume and job description
  - Identify skill gaps and matches
  - Suggest specific improvements to increase relevance
- **LangGraph Node**: `scoring_node`

### Agent 2: Resume Modifier
- **Input**: Original resume, selected suggestions from Agent 1
- **Output**: Modified resume (markdown)
- **Responsibilities**:
  - Apply approved changes from Agent 1's suggestions
  - Optimize content to fit 1 page
  - Maximize relevance while maintaining brevity
  - Preserve professional formatting
- **LangGraph Node**: `modification_node`

### Agent 3: Re-scorer
- **Input**: Modified resume, original job description
- **Output**:
  - New compatibility score (1-100)
  - Comparison with original score
  - Improvement analysis
  - Remaining concerns
- **Responsibilities**:
  - Evaluate improvement from modifications
  - Present before/after comparison
  - Identify remaining concerns
  - Recommend next steps
- **LangGraph Node**: `rescoring_node`

### Agent 5: Resume Optimizer
- **Input**: Modified resume, job description, current score
- **Output (Suggestion Phase)**:
  - List of optimization suggestions with checkboxes
  - Analysis of optimization opportunities
  - Current word count
- **Output (Application Phase)**:
  - Optimized resume (with selected optimizations applied)
  - Word count before/after
  - Optimization summary
  - List of changes made
- **Responsibilities**:
  - **Phase 1**: Analyze and suggest specific optimizations (does NOT auto-apply)
  - **Phase 2**: Apply only the user-selected optimization suggestions
  - Remove redundancy and wordiness based on user approval
  - Aim for 1 page (500-700 words)
  - Maintain all critical information
  - Each suggestion is independently selectable
- **LangGraph Nodes**: `optimization_node` (suggest), `apply_optimizations_node` (apply)

### Agent 4: Formatting Validator
- **Input**: Modified resume (markdown)
- **Output**:
  - Validation score (1-100)
  - List of issues (Critical, Warning, Info)
  - Formatting recommendations
  - Overall validity status
- **Responsibilities**:
  - Check formatting consistency
  - Validate professional appearance
  - Ensure proper structure
  - Verify no typos or errors
  - Check resume length (1 page ideal)
- **LangGraph Node**: `validation_node`

### Process 5: PDF Export
- **Input**: Approved resume (markdown)
- **Output**: Professional PDF document
- **Responsibilities**:
  - Convert markdown to PDF with professional styling
  - Generate both file and bytes for download
  - Ensure ATS-friendly formatting
- **LangGraph Node**: `export_pdf_node`

### Agent 7: Cover Letter Writer (Optional)
- **Input**: Optimized resume (markdown), job description
- **Output (Generation Phase)**:
  - Tailored cover letter draft (markdown)
  - Cover letter summary (approach and key points)
- **Output (Revision Phase)**:
  - Revised cover letter (markdown)
  - Revision notes (what was changed)
- **Responsibilities**:
  - Generate personalized cover letter based on resume and job
  - Highlight candidate's most relevant qualifications
  - Address key requirements from job description
  - Create cohesive narrative about candidate's career
  - Show enthusiasm and cultural fit
  - Keep it concise (250-350 words, 3-4 paragraphs)
  - Revise based on Agent 8 feedback + user feedback
  - Preserve identified strengths while fixing issues
- **LangGraph Nodes**: `cover_letter_generation_node`, `revise_cover_letter_node`

### Agent 8: Cover Letter Reviewer (Optional)
- **Input**: Cover letter draft, job description, resume (for context)
- **Output**:
  - Overall quality assessment
  - Critical issues (must fix - dealbreakers)
  - Content issues (should fix - weakens letter)
  - Minor issues (nice to fix - polish)
  - Strengths (what works well)
  - Revision needed flag + priority level
- **Responsibilities**:
  - Review cover letter for quality and professionalism
  - Identify factual errors, placeholder text, incorrect dates
  - Flag content problems (too long, weak opening, generic statements)
  - Suggest improvements for tone, formatting, word choice
  - Highlight effective elements to preserve
  - Determine if revision is critical, moderate, minor, or unnecessary
- **LangGraph Node**: `review_cover_letter_node`

## LangGraph Integration

### State Management

The workflow uses a **typed state dictionary** (`WorkflowState`) that tracks:
- Input data (resume, job description)
- Agent outputs (scores, suggestions, modifications)
- Workflow control (current stage, approval status, errors)
- Messages for audit trail

### Workflow Phases

1. **Analysis Workflow**: Input → Fetch Job → Score → END
2. **Modification Workflow**: Modify → Rescore → Suggest Optimizations → END
3. **Optimization Application Workflow**: Apply Optimizations → Validate → END
4. **Export Workflow**: Export → END
5. **Cover Letter Workflow** (Optional): Generate Cover Letter → Review → END
6. **Cover Letter Revision Workflow** (Optional): Revise (with feedback) → END
7. **Cover Letter Export Workflow** (Optional): Export PDF → END

Each phase can be invoked independently with human-in-the-loop checkpoints between phases.

### Human-in-the-Loop

LangGraph enables natural **checkpoints** where:
- User selects which suggestions to apply (after Agent 1)
- User selects which optimizations to apply (after Agent 5 suggestions)
- User approves or rejects modifications (after Agent 4 validation)
- User decides when to export
- User optionally generates a cover letter

The state persists between invocations, allowing resumable workflows.

## Technology Stack

- **Orchestration**: LangGraph
- **LLM Framework**: LangChain Core
- **Frontend**: Streamlit
- **LLM**: Google Gemini API (via LangChain)
- **PDF Generation**: WeasyPrint
- **Web Scraping**: beautifulsoup4, requests
- **Environment**: Python 3.8+

## Project Structure

```
resume-customizer/
├── agents/
│   ├── __init__.py
│   ├── agent_1_scorer.py      # Resume scoring and analysis
│   ├── agent_2_modifier.py    # Resume modification
│   ├── agent_3_rescorer.py    # Re-evaluation
│   ├── agent_4_validator.py   # Formatting validation
│   ├── agent_5_optimizer.py   # Length optimization
│   ├── agent_6_freeform.py    # Freeform editing
│   ├── agent_7_cover_letter.py # Cover letter generation & revision
│   └── agent_8_reviewer.py    # Cover letter review & feedback
├── workflow/
│   ├── __init__.py
│   ├── state.py               # LangGraph state definitions
│   ├── nodes.py               # LangGraph node functions
│   ├── graph.py               # LangGraph workflow definition
│   └── orchestrator.py        # High-level orchestrator API
├── utils/
│   ├── __init__.py
│   ├── gemini_client.py       # Gemini API wrapper
│   ├── pdf_exporter.py        # PDF generation
│   └── job_scraper.py         # Job description fetching
├── data/
│   └── resumes/               # Storage for resumes
├── app.py                     # Streamlit frontend
├── main.py                    # Core application logic
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── CLAUDE.md                 # This file
```

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd resume-customizer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Usage

### Via Streamlit UI

1. Upload your resume in markdown format
2. Provide the job description URL or paste manually
3. Agent 1 analyzes and scores your resume (Initial Scoring)
4. **Checkpoint**: Review and select suggested changes
5. Agent 2 modifies your resume based on selections
6. Agent 3 rescores and presents improvements (Second Scoring)
7. Agent 5 analyzes and suggests optimization opportunities
8. **Checkpoint**: Review and select which optimizations to apply
9. Agent 5 applies selected optimizations to make resume concise
10. Agent 4 validates formatting and consistency
11. **Checkpoint**: Review validation results and approve
12. Export to PDF
13. **Optional**: Generate a tailored cover letter with Agent 7
14. Agent 8 automatically reviews the cover letter for quality
15. **Checkpoint**: Review feedback, optionally add your own notes
16. Either revise cover letter (loops back to step 14) or approve & export
17. Download both resume and cover letter as PDFs

### Programmatic Usage (LangGraph)

```python
from main import ResumeCustomizer

# Initialize
customizer = ResumeCustomizer()

# Start workflow
state = customizer.start_workflow(
    resume=resume_content,
    job_description=job_desc
)

# Review suggestions, then continue
state = customizer.continue_workflow(state)

# Approve and export
final_state = customizer.finalize_workflow(state)

# Download PDF
pdf_bytes = final_state['pdf_bytes']

# Optional: Generate cover letter
cover_letter_state = customizer.orchestrator.generate_cover_letter(final_state)
cover_letter_pdf = cover_letter_state['cover_letter_pdf_bytes']
```

### Full Automation (Testing)

```python
# Run complete workflow without human interaction
final_state = customizer.run_complete_workflow(
    resume=resume_content,
    job_description=job_desc,
    auto_select_all=True,
    auto_approve=True
)
```

## Features

- ✅ Multi-agent AI system with LangGraph orchestration
- ✅ Stateful workflow with checkpoints
- ✅ Human-in-the-loop decision points
- ✅ Real-time scoring and feedback
- ✅ Maintains 1-page format
- ✅ Professional PDF export for resumes
- ✅ **Optional cover letter generation** with PDF export
- ✅ Interactive checkbox interface for suggested changes
- ✅ Before/after comparison
- ✅ Message audit trail
- ✅ Error handling and recovery
- ✅ Legacy compatibility layer

## API Requirements

- **Gemini API Key**: Required for LLM operations
  - Get your key from: https://makersuite.google.com/app/apikey
  - Model: gemini-2.0-flash-exp (configurable)

## Development Notes

### LangGraph Benefits

1. **State Management**: Automatic state persistence between steps
2. **Checkpoints**: Natural human-in-the-loop integration
3. **Modularity**: Each agent is an independent node
4. **Extensibility**: Easy to add new agents or branches
5. **Debugging**: Message trail for observability
6. **Streaming**: Future support for streaming updates

### Agent Design

- Each agent is **stateless** - receives state, returns updates
- Agents use **Google Gemini** for LLM capabilities
- Prompts are engineered for specific tasks
- Error handling at node level with fallback states

### Workflow Control

- **Conditional routing** based on state values
- **Multi-phase execution** with separate compiled graphs
- **Approval gates** between major phases
- **State updates** between invocations for user input

## Future Enhancements

- Support for multiple resume formats (PDF, DOCX input)
- Template selection for different industries
- A/B testing multiple versions
- Integration with job boards
- Resume version history
- LangGraph streaming for real-time updates
- Persistent state storage (SQLite/Postgres)
- Multi-user support
- API endpoints for programmatic access

## LangGraph Workflow Details

### State Schema

```python
WorkflowState = TypedDict({
    # Inputs
    "original_resume": str,
    "job_description": str,
    "job_url": Optional[str],

    # Agent 1 outputs
    "initial_score": int,
    "analysis": str,
    "suggestions": List[Dict],

    # Agent 2 outputs
    "modified_resume": str,

    # Agent 3 outputs
    "new_score": int,
    "score_improvement": int,
    "improvements": List[str],
    "concerns": List[str],
    "recommendation": str,

    # Agent 5 outputs (Optimization suggestions phase)
    "optimization_suggestions": List[Dict],
    "optimization_analysis": str,
    "word_count_before_optimization": int,

    # Agent 5 outputs (Optimization application phase)
    "optimized_resume": str,
    "word_count_before": int,
    "word_count_after": int,
    "words_removed": int,
    "optimization_summary": str,
    "optimization_changes": List[str],

    # Agent 4 outputs
    "validation_score": int,
    "is_valid": bool,
    "validation_issues": List[Dict],
    "validation_recommendations": List[str],

    # Agent 7 outputs (Cover Letter)
    "cover_letter": str,
    "cover_letter_summary": str,
    "cover_letter_pdf_path": str,
    "cover_letter_pdf_bytes": bytes,

    # Control
    "current_stage": str,
    "approved": bool,
    "error": Optional[str],
    "messages": List[Dict]
})
```

### Node Functions

All node functions follow the pattern:
```python
def node_function(state: WorkflowState) -> Dict[str, Any]:
    # Process input from state
    # Execute agent logic
    # Return state updates
    return {
        "new_key": value,
        "current_stage": "next_stage",
        "messages": [{"role": "agent", "content": "..."}]
    }
```

### Orchestrator API

The `ResumeWorkflowOrchestrator` class provides:
- `start_analysis()` - Run Agent 1 (scoring and suggestions)
- `apply_modifications()` - Run Agents 2, 3, and 5 (modification, rescoring, optimization suggestions)
- `apply_optimizations()` - Run Agent 5 application and Agent 4 (apply selected optimizations and validate)
- `export_resume()` - Run PDF export
- `generate_cover_letter()` - Run Agent 7 (optional cover letter generation)
- `update_suggestions()` - Helper for UI
- `approve_resume()` - Helper for UI
- `get_workflow_status()` - Current state info
