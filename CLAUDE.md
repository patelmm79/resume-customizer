# Resume Customizer - Agentic Application

## Project Overview

An intelligent resume customization system that uses multiple AI agents to analyze, optimize, and tailor resumes to specific job descriptions.

## Architecture

This application implements a multi-agent system with the following workflow:

### Agent 1: Resume Analyzer & Scorer
- **Input**: Original resume (markdown), job description (URL)
- **Output**:
  - Compatibility score (1-10)
  - Detailed analysis
  - Checkbox list of suggested changes
- **Responsibilities**:
  - Parse and understand both resume and job description
  - Identify skill gaps and matches
  - Suggest specific improvements to increase relevance

### Agent 2: Resume Modifier
- **Input**: Original resume, suggestions from Agent 1
- **Output**: Modified resume (markdown)
- **Responsibilities**:
  - Apply approved changes from Agent 1's suggestions
  - Optimize content to fit 1 page
  - Maximize relevance while maintaining brevity
  - Preserve professional formatting

### Agent 3: Re-scorer & Approval
- **Input**: Modified resume, original job description
- **Output**:
  - New compatibility score (1-10)
  - Comparison with original score
  - Approval request
- **Responsibilities**:
  - Evaluate improvement from modifications
  - Present before/after comparison
  - Request user approval

### Process 4: PDF Export
- **Input**: Approved resume (markdown)
- **Output**: Professional PDF document
- **Responsibilities**:
  - Convert markdown to PDF
  - Ensure professional formatting
  - Save to specified location

## Technology Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini API
- **PDF Generation**: markdown-pdf or reportlab
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

1. Upload your resume in markdown format
2. Provide the job description URL
3. Agent 1 analyzes and scores your resume
4. Review and select suggested changes
5. Agent 2 modifies your resume
6. Agent 3 rescores and presents the improved version
7. Approve and export to PDF

## Features

- Multi-agent AI system for intelligent resume optimization
- Real-time scoring and feedback
- Maintains 1-page format
- Professional PDF export
- Interactive checkbox interface for suggested changes
- Before/after comparison

## API Requirements

- **Gemini API Key**: Required for LLM operations
  - Get your key from: https://makersuite.google.com/app/apikey
  - Model: gemini-2.0-flash-exp

## Development Notes

- Each agent is modular and can be tested independently
- Prompts are carefully engineered for specific tasks
- Token usage is optimized for cost efficiency
- Error handling for API failures and network issues

## Future Enhancements

- Support for multiple resume formats (PDF, DOCX input)
- Template selection for different industries
- A/B testing multiple versions
- Integration with job boards
- Resume version history
