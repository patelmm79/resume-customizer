# Resume Customizer

An intelligent, multi-agent AI system orchestrated by **LangGraph** that analyzes, optimizes, and tailors resumes to specific job descriptions using multiple LLM providers (Gemini, Claude, or custom/local LLMs).

## 🎉 NEW: Structured Output Support

**ALL AI models now work with this application!** We've implemented JSON Schema-based structured output using the `response_format` parameter.

### ✅ Now Fully Supported
- **DeepSeek R1** ✅ (reasoning models now work!)
- **OpenAI o1** ✅ (reasoning models now work!)
- **Gemini 2.0 Flash** (fast, reliable, free tier)
- **Claude Sonnet 4.5** (highest quality)
- **GPT-4o / GPT-4o Mini** (excellent balance)

### How It Works
Instead of relying on prompt engineering, we use **JSON Schema validation** via the `response_format` parameter. This **guarantees** valid JSON output from any model, including reasoning models that previously only returned plain text.

**📖 See [STRUCTURED_OUTPUT_UPDATE.md](STRUCTURED_OUTPUT_UPDATE.md) for complete details on this breakthrough.**

**📖 See [MODEL_SELECTION_GUIDE.md](MODEL_SELECTION_GUIDE.md) for model comparison and setup instructions.**

**📚 For the original debugging journey, see [LESSONS_LEARNED.md](LESSONS_LEARNED.md).**

## Features

- **LangGraph Orchestration**: Stateful workflow with human-in-the-loop checkpoints
- **Multi-Model LLM Support**: Choose from multiple AI providers
  - Google Gemini (gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash)
  - Anthropic Claude (claude-3-5-sonnet, claude-3-5-haiku, claude-3-opus)
  - Custom/Local LLMs (OpenAI, LM Studio, Ollama, Azure OpenAI, etc.)
- **6-Agent AI System**: Specialized agents working together
  - **Agent 1**: Analyzes and scores resumes (initial, second, and final scoring)
  - **Agent 2**: Modifies resumes based on selected suggestions
  - **Agent 4**: Validates formatting, consistency, and professionalism
  - **Agent 5**: Optimizes resume length (target 1 page / 500-700 words)
  - **Agent 6**: Applies user-requested freeform changes iteratively
- **Interactive UI**: Built with Streamlit for easy interaction
- **Granular Skill Control**: Individual checkboxes for each skill suggestion
- **Live Preview**: Side-by-side validation with markdown preview
- **Iterative Editing**: Request unlimited custom changes before export
- **Smart Optimization**: Automatically optimizes for 1-page format while maintaining score
- **PDF & Markdown Export**: Export in multiple formats
- **Job Scraping**: Fetch job descriptions directly from URLs
- **Message Trail**: Full observability of workflow execution

## Architecture

```
┌──────────────────────────────────────┐
│         Streamlit UI                 │
│  (Multi-Model LLM Selection)         │
└──────────────┬───────────────────────┘
               │
    ┌──────────▼──────────┐
    │  LLM Client Layer   │
    │ (Gemini/Claude/     │
    │  Custom)            │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   LangGraph         │
    │   Orchestrator      │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Agent 1: Scorer     │ Initial Analysis & Score (1-100)
    │                     │ + Individual Skill Suggestions
    └──────────┬──────────┘
               │
    [Human Checkpoint: Select Suggestions]
               │
    ┌──────────▼──────────┐
    │ Agent 2: Modifier   │ Apply Selected Changes
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Agent 1: Scorer     │ Second Scoring (score_only)
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Agent 5: Optimizer  │ Length Optimization (1 page)
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Agent 4: Validator  │ Format & Consistency Check
    └──────────┬──────────┘
               │
    [Human Checkpoint: Review Results]
               │
    ┌──────────▼──────────┐
    │ Agent 6: Freeform   │ Iterative Custom Edits
    │ Editor (Optional)   │ (Loop until user says done)
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Agent 1: Scorer     │ Final Scoring (score_only)
    └──────────┬──────────┘
               │
    [Human Checkpoint: Approve]
               │
    ┌──────────▼──────────┐
    │   PDF/Markdown      │ Export to Files
    │   Export            │
    └─────────────────────┘
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd resume-customizer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env  # On Windows: copy .env.example .env

   # Edit .env and add your API key(s) for the LLM provider(s) you want to use
   ```

   Your `.env` file should contain at least one LLM configuration:

   **For Gemini (Google AI)**:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-exp
   ```
   Get your API key from: https://makersuite.google.com/app/apikey

   **For Claude (Anthropic)**:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   CLAUDE_MODEL=claude-3-5-sonnet-20241022
   ```
   Get your API key from: https://console.anthropic.com/

   **For Custom/Local LLM** (OpenAI, LM Studio, Ollama, etc.):
   ```
   CUSTOM_LLM_API_KEY=your_custom_api_key_here
   CUSTOM_LLM_BASE_URL=http://localhost:1234/v1
   CUSTOM_LLM_MODEL=your-model-name
   ```

   See `.env.example` for complete configuration examples including OpenAI, Azure OpenAI, LM Studio, and Ollama.

## Usage

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Select Your LLM Provider**
   - In the sidebar, choose your preferred LLM provider (Gemini, Claude, or Custom)
   - Select the specific model you want to use
   - Verify configuration status shows "✅ Configured"

3. **Follow the workflow**
   - **Step 1-2**: Upload your resume (markdown) and provide job description
   - **Step 3**: Initial Scoring - Review compatibility score and suggestions
   - **Step 4**: Select Suggestions - Choose which improvements to apply (individual skill selection)
   - **Step 5**: Modifying Resume - Agent 2 applies your selected changes
   - **Step 6**: Second Scoring - See improved score after modifications
   - **Step 7**: Optimizing Length - Agent 5 optimizes for 1-page format
   - **Step 8**: Validating - Agent 4 checks formatting and consistency
   - **Step 9**: Review & Approve - See validation results with live preview
   - **Step 10**: Final Edits (Optional) - Request custom changes iteratively via Agent 6
   - **Step 11**: Final Score - See progression from initial to final score
   - **Step 12**: Export - Download as PDF and/or Markdown

## Project Structure

```
resume-customizer/
├── agents/
│   ├── __init__.py
│   ├── agent_1_scorer.py      # Resume scoring and analysis (all scoring steps)
│   ├── agent_2_modifier.py    # Resume modification
│   ├── agent_4_validator.py   # Formatting and consistency validation
│   ├── agent_5_optimizer.py   # Resume length optimization
│   └── agent_6_freeform.py    # User-requested custom changes
├── workflow/
│   ├── __init__.py
│   ├── state.py              # WorkflowState TypedDict definition
│   ├── nodes.py              # Agent execution nodes
│   └── graph.py              # LangGraph workflow definitions
├── utils/
│   ├── __init__.py
│   ├── llm_client.py         # Multi-provider LLM abstraction layer
│   ├── agent_helper.py       # Agent-to-LLM client bridge
│   ├── gemini_client.py      # Gemini API wrapper
│   ├── pdf_exporter.py       # PDF generation (ReportLab)
│   └── job_scraper.py        # Job description fetching
├── data/
│   └── resumes/              # Resume storage
│       └── sample_resume.md  # Example resume
├── app.py                    # Streamlit frontend
├── main.py                   # Core application logic
├── requirements.txt          # Python dependencies
├── .env.example             # Environment configuration template
├── CLAUDE.md                # Project documentation
├── LANGGRAPH_ARCHITECTURE.md # LangGraph architecture details
└── README.md                # This file
```

## How It Works

### Agent 1: Resume Scorer (Multi-Purpose)
- **Initial Scoring**: Analyzes resume against job description, provides score (1-100)
- **Individual Skill Suggestions**: Creates separate checkbox for each skill from job description
- **Second Scoring**: Re-evaluates after modifications using `score_only()` method
- **Final Scoring**: Provides final score after all edits using `score_only()` method
- Categorizes suggestions (Skills, Experience, Summary, etc.)

### Agent 2: Resume Modifier
- Applies ONLY user-selected suggestions from Agent 1
- Critical safeguards prevent adding unchecked skills
- Maintains professional formatting
- Focuses on relevance and impact
- User has granular control over every change

### Agent 4: Formatting Validator
- Validates formatting, consistency, and professional appearance
- Returns validation score (1-100) and categorized issues (CRITICAL, WARNING, INFO)
- Checks: formatting, length, consistency, professionalism, readability
- Provides actionable recommendations
- User can proceed to export or review issues

### Agent 5: Resume Optimizer
- Optimizes resume length while maintaining compatibility score
- Targets 1-page format (500-700 words ideal)
- Removes redundancy and verbose language
- Tracks word count reduction
- Returns optimization summary and change list

### Agent 6: Freeform Editor (Optional)
- Applies user-requested custom changes iteratively
- Maintains change history for full traceability
- User can request unlimited modifications
- "Reset to Optimized" option available
- Loops until user clicks "Finalize & Score"

### Multi-Model LLM Support
- Abstract LLM client layer supports multiple providers
- Seamless switching between Gemini, Claude, and custom LLMs
- Configuration status indicator in UI
- OpenAI-compatible API support for local LLMs (LM Studio, Ollama, etc.)

### PDF & Markdown Export
- Converts markdown to professional PDF using ReportLab
- Applies clean, ATS-friendly styling
- Cross-platform (Windows, macOS, Linux)
- Also exports markdown source for version control
- Saves locally and provides download buttons

## Requirements

- Python 3.8 or higher
- At least one LLM API key:
  - Gemini API key (recommended, free tier available)
  - Anthropic Claude API key (optional)
  - Custom LLM endpoint (optional, for local models)
- Internet connection (for API calls and job scraping)

## Dependencies

See `requirements.txt` for full list:

**Core**:
- `streamlit>=1.28.0` - Web interface
- `langgraph>=0.2.0` - Agent orchestration
- `langchain-core>=0.3.0` - LangChain core
- `langchain-google-genai>=2.0.0` - Gemini integration
- `python-dotenv>=1.0.0` - Environment management

**LLM Providers**:
- `google-generativeai>=0.3.0` - Gemini API
- `anthropic>=0.40.0` - Claude API (optional)
- `openai>=1.0.0` - OpenAI and compatible APIs (optional)

**Utilities**:
- `requests>=2.31.0` - HTTP requests
- `beautifulsoup4>=4.12.0` - Job description scraping
- `markdown>=3.5.0` - Markdown processing
- `reportlab>=4.0.0` - PDF generation
- `pillow>=9.0.0` - Image handling for PDFs

## Tips for Best Results

1. **Resume Format**: Use markdown format with clear sections (## Headings)
2. **LLM Selection**: Choose based on your needs:
   - Gemini 2.0 Flash: Fast, cost-effective, great results
   - Claude Sonnet 3.5: Most capable, excellent writing quality
   - Local LLMs: Privacy-focused, works offline after model download
3. **Skill Selection**: Be selective with individual skill checkboxes - only approve skills you actually have
4. **Job URLs**: Provide clean job posting URLs when possible, or paste description directly
5. **Validation Review**: Pay attention to CRITICAL validation issues before export
6. **Freeform Edits**: Use Agent 6 for final polish and personalization
7. **Iterative Refinement**: Don't hesitate to use "Reset to Optimized" and try different approaches
8. **1-Page Target**: Agent 5 aims for 500-700 words (ideal for single page)

## Example Resume Format

```markdown
# Your Name

Email: email@example.com | Phone: (555) 123-4567 | Location: City, State

## Professional Summary
Brief summary of your experience and skills...

## Work Experience
### Job Title | Company Name
*Start Date - End Date*
- Achievement or responsibility
- Another achievement

## Education
### Degree | University Name
Graduation Date

## Skills
- Category: skill1, skill2, skill3

## Projects (optional)
### Project Name
Description
```

## Troubleshooting

### "Failed to parse response" Error
**Cause**: You're using an incompatible reasoning model (DeepSeek R1, OpenAI o1, etc.)

**Solution**:
1. Open the Streamlit sidebar
2. Switch to **Gemini** or **Claude** provider
3. Select a compatible model (see [MODEL_SELECTION_GUIDE.md](MODEL_SELECTION_GUIDE.md))
4. Try again

**Why it happens**: Reasoning models output thinking process in plain text instead of JSON format. See [LESSONS_LEARNED.md](LESSONS_LEARNED.md) for technical details.

### LLM Configuration Issues
- **"❌ Missing API Key"**: Check that your `.env` file contains the correct API key
- **Gemini errors**: Verify your API key at https://makersuite.google.com/app/apikey
- **Claude errors**: Verify your API key at https://console.anthropic.com/
- **Custom LLM errors**: Check that `CUSTOM_LLM_BASE_URL` is accessible and model is running
- Check your API quota and limits
- Ensure you have internet connectivity (unless using local LLMs)
- **Wrong model selected**: See [MODEL_SELECTION_GUIDE.md](MODEL_SELECTION_GUIDE.md) for compatible models

### PDF Generation Issues
- PDF export uses ReportLab (pure Python, no system dependencies required)
- If PDF generation fails, check that `pillow` is installed: `pip install pillow`
- Ensure your resume markdown is valid

### Job Scraping Failures
- Some websites block automated scraping
- Try pasting the job description manually instead
- Ensure the URL is accessible

### Local LLM Setup (LM Studio / Ollama)
- **LM Studio**: Start server, use `http://localhost:1234/v1`
- **Ollama**: Start server, use `http://localhost:11434/v1`
- Set `CUSTOM_LLM_API_KEY` to any non-empty value
- Set `CUSTOM_LLM_MODEL` to your loaded model name

### Agent Workflow Issues
- If workflow gets stuck, check the console for error messages
- Ensure all selected LLM provider is properly configured
- Try switching to a different LLM provider if one isn't working

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

- Built with **LangGraph** for agent orchestration
- **Google Gemini**, **Anthropic Claude**, and **OpenAI-compatible APIs** for LLM support
- **Streamlit** for the interactive frontend
- **ReportLab** for cross-platform PDF generation

## Key Features Added in Latest Version

- **Multi-Model LLM Support**: Seamlessly switch between Gemini, Claude, and custom/local LLMs
- **Individual Skill Selection**: Granular control over which skills to add from job description
- **Agent 5 - Optimizer**: Automatic length optimization targeting 1-page format
- **Agent 6 - Freeform Editor**: Iterative custom editing with change history
- **Live Validation Preview**: Side-by-side validation results with markdown preview
- **Unified Scoring**: Agent 1 handles all scoring operations (initial, second, final)
- **Enhanced UI**: Clear stage labels and progress tracking through all 12 steps

## Future Enhancements

- Support for PDF/DOCX resume input
- Multiple resume templates
- Cover letter generation
- A/B testing feature
- Integration with job boards (LinkedIn, Indeed, etc.)
- Resume version history with git integration
- Browser extension for one-click optimization
- Batch processing for multiple job applications
- Custom scoring criteria configuration

## Contact

For questions or support, please open an issue on GitHub.

---

**Happy Job Hunting!** 🚀
