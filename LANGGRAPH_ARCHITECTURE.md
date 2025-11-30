# LangGraph Architecture - Resume Customizer

## Overview

This document details the LangGraph implementation for the Resume Customizer application, explaining how agents are orchestrated through a stateful workflow with human-in-the-loop checkpoints.

## Why LangGraph?

### Benefits Over Manual Orchestration

| Feature | Manual (Pre-LangGraph) | LangGraph |
|---------|----------------------|-----------|
| **State Management** | Streamlit session state | Typed state dictionary with automatic persistence |
| **Checkpoints** | Manual stage tracking | Built-in human-in-the-loop support |
| **Modularity** | Monolithic functions | Independent node functions |
| **Extensibility** | Hard to add branches | Easy conditional routing |
| **Debugging** | Limited visibility | Message trail + graph visualization |
| **Streaming** | Not supported | Future-ready |
| **Error Handling** | Try-catch per agent | Node-level error states |
| **Resumability** | Page refresh loses progress | State persists across invocations |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Resume Customizer                        │
│                     LangGraph Orchestration                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        WORKFLOW PHASES                           │
└─────────────────────────────────────────────────────────────────┘

Phase 1: ANALYSIS
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   START     │────▶│  fetch_job_desc │────▶│  scoring_node    │
│  (Input)    │     │  (if URL given) │     │  [Agent 1]       │
└─────────────┘     └─────────────────┘     └──────────┬───────┘
                                                        │
                                                        ▼
                                             ┌──────────────────┐
                                             │       END        │
                                             │ (Human selects)  │
                                             └──────────────────┘

Phase 2: MODIFICATION & RESCORING
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   START     │────▶│ modification_   │────▶│  rescoring_node  │
│ (Selected)  │     │    node         │     │  [Agent 3]       │
│             │     │  [Agent 2]      │     │                  │
└─────────────┘     └─────────────────┘     └──────────┬───────┘
                                                        │
                                                        ▼
                                             ┌──────────────────┐
                                             │       END        │
                                             │ (Human approves) │
                                             └──────────────────┘

Phase 3: EXPORT
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   START     │────▶│  export_pdf_    │────▶│       END        │
│ (Approved)  │     │     node        │     │  (PDF ready)     │
└─────────────┘     └─────────────────┘     └──────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                      STATE FLOW DIAGRAM                          │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │  WorkflowState   │
                    │  ┌─────────────┐ │
                    │  │ Input Data  │ │
                    │  └─────────────┘ │
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │   Agent 1: Scoring       │
              │   ┌──────────────────┐   │
              │   │ + initial_score  │   │
              │   │ + analysis       │   │
              │   │ + suggestions[]  │   │
              │   └──────────────────┘   │
              └──────────┬───────────────┘
                         │
                  [Human Selection]
                         │
                         ▼
              ┌──────────────────────────┐
              │   Agent 2: Modification  │
              │   ┌──────────────────┐   │
              │   │+ modified_resume │   │
              │   └──────────────────┘   │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │   Agent 3: Rescoring     │
              │   ┌──────────────────┐   │
              │   │ + new_score      │   │
              │   │ + improvements[] │   │
              │   │ + concerns[]     │   │
              │   │ + recommendation │   │
              │   └──────────────────┘   │
              └──────────┬───────────────┘
                         │
                  [Human Approval]
                         │
                         ▼
              ┌──────────────────────────┐
              │   PDF Export             │
              │   ┌──────────────────┐   │
              │   │ + pdf_path       │   │
              │   │ + pdf_bytes      │   │
              │   └──────────────────┘   │
              └──────────────────────────┘
```

## Component Breakdown

### 1. State Definition (`workflow/state.py`)

```python
class WorkflowState(TypedDict):
    # INPUT: What the user provides
    original_resume: str
    job_description: str
    job_url: Optional[str]

    # AGENT 1 OUTPUTS: Scoring & Analysis
    initial_score: Optional[int]
    analysis: Optional[str]
    suggestions: Optional[List[SuggestionDict]]

    # AGENT 2 OUTPUTS: Modified Resume
    modified_resume: Optional[str]

    # AGENT 3 OUTPUTS: Rescoring & Evaluation
    new_score: Optional[int]
    score_improvement: Optional[int]
    comparison: Optional[str]
    improvements: Optional[List[str]]
    concerns: Optional[List[str]]
    recommendation: Optional[str]
    reasoning: Optional[str]

    # PDF EXPORT OUTPUTS
    pdf_path: Optional[str]
    pdf_bytes: Optional[bytes]

    # WORKFLOW CONTROL
    current_stage: str  # Tracks where we are
    approved: bool      # User approval flag
    error: Optional[str]  # Error messages
    messages: Annotated[List[Dict], add_messages]  # Audit trail
```

### 2. Node Functions (`workflow/nodes.py`)

Each node is a pure function: `State → State Updates`

```python
def scoring_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 1: Score and analyze resume."""
    agent = ResumeScorerAgent()
    result = agent.analyze_and_score(
        state["original_resume"],
        state["job_description"]
    )

    return {
        "initial_score": result["score"],
        "analysis": result["analysis"],
        "suggestions": result["suggestions"],
        "current_stage": "awaiting_selection",
        "messages": [{"role": "agent_1", "content": f"Score: {result['score']}"}]
    }
```

**Key Nodes:**
- `fetch_job_description_node` - Scrapes job URL
- `scoring_node` - Agent 1
- `modification_node` - Agent 2
- `rescoring_node` - Agent 3
- `export_pdf_node` - PDF generation

### 3. Graph Definition (`workflow/graph.py`)

Three separate compiled graphs for each phase:

```python
# Phase 1: Analysis
analysis_workflow = StateGraph(WorkflowState)
analysis_workflow.add_node("fetch_job", fetch_job_description_node)
analysis_workflow.add_node("scoring", scoring_node)
analysis_workflow.set_conditional_entry_point(...)
analysis_workflow.add_edge("fetch_job", "scoring")
analysis_workflow.add_edge("scoring", END)
analysis_workflow = analysis_workflow.compile()

# Phase 2: Modification + Rescoring
modification_workflow = StateGraph(WorkflowState)
modification_workflow.add_node("modify", modification_node)
modification_workflow.add_node("rescoring", rescoring_node)
modification_workflow.set_entry_point("modify")
modification_workflow.add_edge("modify", "rescoring")
modification_workflow.add_edge("rescoring", END)
modification_workflow = modification_workflow.compile()

# Phase 3: Export
export_workflow = StateGraph(WorkflowState)
export_workflow.add_node("export", export_pdf_node)
export_workflow.set_entry_point("export")
export_workflow.add_edge("export", END)
export_workflow = export_workflow.compile()
```

### 4. Orchestrator (`workflow/orchestrator.py`)

High-level API that manages the workflows:

```python
class ResumeWorkflowOrchestrator:
    def __init__(self):
        self.analysis_workflow = analysis_workflow
        self.modification_workflow = modification_workflow
        self.export_workflow = export_workflow

    def start_analysis(self, resume, job_description, job_url):
        """Phase 1: Run Agent 1"""
        state = create_initial_state(resume, job_description, job_url)
        return self.analysis_workflow.invoke(state)

    def apply_modifications(self, state):
        """Phase 2: Run Agent 2 + Agent 3"""
        return self.modification_workflow.invoke(state)

    def export_resume(self, state):
        """Phase 3: Export to PDF"""
        return self.export_workflow.invoke(state)
```

### 5. Integration Layer (`main.py`)

User-friendly interface:

```python
class ResumeCustomizer:
    def __init__(self):
        self.orchestrator = ResumeWorkflowOrchestrator()

    def start_workflow(self, resume, job_description, job_url):
        return self.orchestrator.start_analysis(...)

    def continue_workflow(self, state):
        return self.orchestrator.apply_modifications(state)

    def finalize_workflow(self, state):
        state = self.orchestrator.approve_resume(state)
        return self.orchestrator.export_resume(state)
```

### 6. Streamlit UI (`app.py`)

Maps workflow stages to UI screens:

```python
current_stage = get_current_stage()

if current_stage == "input":
    # Show upload form
elif current_stage == "awaiting_selection":
    # Show suggestions with checkboxes
elif current_stage == "awaiting_approval":
    # Show before/after comparison
elif current_stage == "completed":
    # Show download button
```

## Execution Flow

### Full Workflow Example

```python
from main import ResumeCustomizer

customizer = ResumeCustomizer()

# 1. Start Analysis (Phase 1)
state = customizer.start_workflow(
    resume="# John Doe...",
    job_description="Looking for Python developer..."
)

print(state["initial_score"])  # 7
print(state["suggestions"])    # List of improvements
print(state["current_stage"])  # "awaiting_selection"

# 2. User selects suggestions (UI interaction)
state["suggestions"][0]["selected"] = True
state["suggestions"][1]["selected"] = False
# ...

# 3. Apply Modifications (Phase 2)
state = customizer.continue_workflow(state)

print(state["modified_resume"])  # Updated content
print(state["new_score"])        # 9
print(state["current_stage"])    # "awaiting_approval"

# 4. User approves (UI interaction)

# 5. Export PDF (Phase 3)
final_state = customizer.finalize_workflow(state)

print(final_state["pdf_path"])   # "data/resumes/resume_20231120.pdf"
print(final_state["current_stage"])  # "completed"
```

## State Transitions

```
input
  ↓
fetch_job (if URL provided)
  ↓
scoring
  ↓
awaiting_selection ← HUMAN CHECKPOINT
  ↓
modification
  ↓
rescoring
  ↓
awaiting_approval ← HUMAN CHECKPOINT
  ↓
export
  ↓
completed
```

## Error Handling

Each node can return error state:

```python
def scoring_node(state):
    try:
        # ... agent logic
        return {...}
    except Exception as e:
        return {
            "error": f"Scoring failed: {str(e)}",
            "current_stage": "error",
            "messages": [{"role": "system", "content": f"Error: {str(e)}"}]
        }
```

The UI checks for errors:

```python
if current_stage == "error":
    st.error(state.get("error"))
    # Show retry button
```

## Message Trail

Every operation adds to the message trail:

```python
"messages": [
    {"role": "system", "content": "Job description fetched successfully"},
    {"role": "agent_1", "content": "Initial score: 70/100"},
    {"role": "agent_2", "content": "Resume modified successfully"},
    {"role": "agent_3", "content": "New score: 90/100 (improvement: +20)"},
    {"role": "system", "content": "PDF exported: data/resumes/resume.pdf"}
]
```

This provides full observability of the workflow execution.

## Benefits Realized

### 1. Separation of Concerns
- **Agents** (`agents/`) - Pure LLM logic
- **Nodes** (`workflow/nodes.py`) - State transformations
- **Graph** (`workflow/graph.py`) - Workflow structure
- **Orchestrator** (`workflow/orchestrator.py`) - High-level API
- **UI** (`app.py`) - User interface

### 2. Testability
Each component can be tested independently:
- Test agents with mock inputs
- Test nodes with mock state
- Test workflow with mock nodes
- Test orchestrator with mock workflows

### 3. Extensibility
Easy to add new features:
- **New agent?** → Add new node function
- **New branch?** → Add conditional routing
- **New validation?** → Add validator node
- **Parallel execution?** → Use LangGraph's `add_concurrent_edges`

### 4. Debugging
- State is fully inspectable at each step
- Message trail shows execution history
- Graph can be visualized (future: LangSmith)

### 5. Human-in-the-Loop
Natural checkpoints between phases:
- User can modify selections
- User can go back and retry
- User can approve or reject

## Comparison: Before vs After

### Before (Manual Orchestration)
```python
# Monolithic, hard-coded flow
if st.session_state.stage == "scoring":
    agent1 = ResumeScorerAgent()
    result = agent1.analyze_and_score(...)
    st.session_state.scoring_result = result
    st.session_state.stage = "modification"
    st.rerun()
```

**Issues:**
- Tight coupling between UI and logic
- State scattered across session
- Hard to test
- No audit trail
- Manual error handling everywhere

### After (LangGraph)
```python
# Clean separation
state = customizer.start_workflow(resume, job_desc)
# State contains everything, fully inspectable
# Workflow handles transitions automatically
# Messages provide audit trail
# Error handling at node level
```

**Benefits:**
- UI just displays state
- Logic is in nodes
- Easy to test
- Full observability
- Centralized error handling

## Future Enhancements

### 1. Persistent State
```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver("resume_workflows.db")
workflow = create_workflow().compile(checkpointer=checkpointer)

# Now workflows can be resumed across sessions!
```

### 2. Streaming
```python
for event in workflow.stream(state):
    print(f"Node: {event['node']}")
    print(f"Updates: {event['updates']}")
    # Update UI in real-time
```

### 3. Conditional Branching
```python
def should_request_more_info(state):
    if state["initial_score"] < 5:
        return "request_clarification"
    return "continue"

workflow.add_conditional_edges(
    "scoring",
    should_request_more_info,
    {
        "request_clarification": "clarification_node",
        "continue": "modification"
    }
)
```

### 4. Parallel Agent Execution
```python
# Run multiple scorers in parallel
workflow.add_concurrent_edges(
    "start",
    ["scorer_1", "scorer_2", "scorer_3"]
)
workflow.add_node("combine_scores", combine_results)
```

## Conclusion

LangGraph transforms the Resume Customizer from a linear script into a robust, extensible, and maintainable agent orchestration system. The architecture is production-ready and easily extensible for future enhancements.
