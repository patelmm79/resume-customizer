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
│  Score & Analyze│ → Score (1-10) + Suggestions
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
│  HUMAN          │ ← User approves
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
┌─────────────┐
│     END     │
└─────────────┘
```

### Agent 1: Resume Analyzer & Scorer
- **Input**: Original resume (markdown), job description (URL or text)
- **Output**:
  - Compatibility score (1-10)
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

### Agent 3: Re-scorer & Approval
- **Input**: Modified resume, original job description
- **Output**:
  - New compatibility score (1-10)
  - Comparison with original score
  - Improvement analysis
  - Approval recommendation
- **Responsibilities**:
  - Evaluate improvement from modifications
  - Present before/after comparison
  - Identify remaining concerns
  - Recommend next steps
- **LangGraph Node**: `rescoring_node`

### Process 4: PDF Export
- **Input**: Approved resume (markdown)
- **Output**: Professional PDF document
- **Responsibilities**:
  - Convert markdown to PDF with professional styling
  - Generate both file and bytes for download
  - Ensure ATS-friendly formatting
- **LangGraph Node**: `export_pdf_node`

## LangGraph Integration

### State Management

The workflow uses a **typed state dictionary** (`WorkflowState`) that tracks:
- Input data (resume, job description)
- Agent outputs (scores, suggestions, modifications)
- Workflow control (current stage, approval status, errors)
- Messages for audit trail

### Workflow Phases

1. **Analysis Workflow**: Input → Fetch Job → Score → END
2. **Modification Workflow**: Modify → Rescore → END
3. **Export Workflow**: Export → END

Each phase can be invoked independently with human-in-the-loop checkpoints between phases.

### Human-in-the-Loop

LangGraph enables natural **checkpoints** where:
- User selects which suggestions to apply
- User approves or rejects modifications
- User decides when to export

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
│   └── agent_3_rescorer.py    # Re-evaluation and approval
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
3. Agent 1 analyzes and scores your resume
4. Review and select suggested changes
5. Agent 2 modifies your resume
6. Agent 3 rescores and presents improvements
7. Approve and export to PDF

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
- ✅ Professional PDF export
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
- `start_analysis()` - Run Agent 1
- `apply_modifications()` - Run Agents 2 & 3
- `export_resume()` - Run PDF export
- `update_suggestions()` - Helper for UI
- `approve_resume()` - Helper for UI
- `get_workflow_status()` - Current state info
