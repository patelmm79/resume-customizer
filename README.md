# Resume Customizer

An intelligent, multi-agent AI system that analyzes, optimizes, and tailors resumes to specific job descriptions using Google Gemini.

## Features

- **Multi-Agent AI System**: Three specialized agents working together
  - **Agent 1**: Analyzes and scores resumes against job descriptions
  - **Agent 2**: Modifies resumes based on selected suggestions
  - **Agent 3**: Re-scores and validates improvements
- **Interactive UI**: Built with Streamlit for easy interaction
- **Checkbox Suggestions**: Select which improvements to apply
- **1-Page Optimization**: Automatically optimizes for single-page format
- **PDF Export**: Professional PDF generation
- **Job Scraping**: Fetch job descriptions directly from URLs

## Architecture

```
┌─────────────────┐
│  Streamlit UI   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Agent 1 │ Score & Analyze (1-10)
    └────┬────┘
         │
    ┌────▼────┐
    │ Agent 2 │ Modify Resume
    └────┬────┘
         │
    ┌────▼────┐
    │ Agent 3 │ Re-score & Approve
    └────┬────┘
         │
    ┌────▼────┐
    │   PDF   │ Export to PDF
    └─────────┘
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
   cp .env.example .env

   # Edit .env and add your Gemini API key
   # Get your API key from: https://makersuite.google.com/app/apikey
   ```

   Your `.env` file should contain:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   GEMINI_MODEL_NAME=gemini-2.0-flash-exp
   ```

## Usage

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Follow the workflow**
   - Upload your resume (markdown format)
   - Provide a job description URL or paste it manually
   - Review the initial score and suggestions
   - Select which improvements to apply
   - Review the modified resume
   - Approve and export to PDF

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
│   └── resumes/               # Resume storage
│       └── sample_resume.md   # Example resume
├── app.py                     # Streamlit frontend
├── main.py                    # Core application logic
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── CLAUDE.md                 # Project documentation
└── README.md                 # This file
```

## How It Works

### Agent 1: Resume Scorer
- Analyzes your resume against the job description
- Provides a compatibility score (1-10)
- Generates specific, actionable suggestions
- Categorizes suggestions (Skills, Experience, Summary, etc.)

### Agent 2: Resume Modifier
- Applies selected suggestions from Agent 1
- Optimizes content for 1-page format
- Maintains professional formatting
- Focuses on relevance and impact

### Agent 3: Re-scorer
- Evaluates the modified resume
- Compares improvement with original
- Provides approval recommendation
- Identifies remaining concerns if any

### PDF Export
- Converts markdown to professional PDF
- Applies clean, ATS-friendly styling
- Saves locally and provides download option

## Requirements

- Python 3.8 or higher
- Google Gemini API key
- Internet connection (for job scraping and API calls)

## Dependencies

See `requirements.txt` for full list:
- `streamlit` - Web interface
- `google-generativeai` - Gemini API
- `beautifulsoup4` - Job description scraping
- `weasyprint` - PDF generation
- `markdown` - Markdown processing
- `python-dotenv` - Environment management

## Tips for Best Results

1. **Resume Format**: Use markdown format with clear sections
2. **Job URLs**: Provide clean job posting URLs when possible
3. **Suggestions**: Review all suggestions before applying
4. **Iterative**: You can go back and modify selections
5. **1-Page Rule**: Agent 2 optimizes for brevity and relevance

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

### API Errors
- Verify your Gemini API key is correct in `.env`
- Check your API quota and limits
- Ensure you have internet connectivity

### PDF Generation Issues
- Install system dependencies for WeasyPrint:
  - Windows: GTK3 runtime
  - macOS: `brew install cairo pango gdk-pixbuf libffi`
  - Linux: `apt-get install libpango-1.0-0 libpangocairo-1.0-0`

### Job Scraping Failures
- Some websites block automated scraping
- Try pasting the job description manually instead
- Ensure the URL is accessible

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

- Built with Google Gemini API
- Streamlit for the frontend
- WeasyPrint for PDF generation

## Future Enhancements

- Support for PDF/DOCX resume input
- Multiple resume templates
- A/B testing feature
- Integration with job boards
- Resume version history
- Browser extension for one-click optimization

## Contact

For questions or support, please open an issue on GitHub.

---

**Happy Job Hunting!** 🚀
