# Quick Start Guide

Get up and running with Resume Customizer in 5 minutes!

## Prerequisites

- Python 3.8 or higher installed
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Setup (5 steps)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
# On Windows
copy .env.example .env

# On macOS/Linux
cp .env.example .env
```

Edit `.env` and add your API key:
```
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### 4. Prepare Your Resume

Convert your resume to markdown format. See `data/resumes/sample_resume.md` for an example.

**Basic Structure:**
```markdown
# Your Name
Contact info

## Professional Summary
Brief summary

## Work Experience
### Job Title | Company
*Dates*
- Achievements

## Education
### Degree | University

## Skills
- Category: skills
```

### 5. Use the Application

1. **Upload** your markdown resume
2. **Provide** job description (URL or paste)
3. **Review** score and suggestions
4. **Select** improvements to apply
5. **Approve** and **export** to PDF

## Workflow Diagram

```
Upload Resume → Fetch Job → Score (1-100) → Select Changes
                                  ↓
                            Modify Resume
                                  ↓
                            Re-score → Approve → Export PDF
```

## Tips

- **First time?** Use the sample resume in `data/resumes/sample_resume.md`
- **Job URLs**: Most career sites work (LinkedIn, Indeed, company sites)
- **Can't scrape?** Just paste the job description manually
- **Not satisfied?** Go back and adjust your selections
- **Keep it brief**: Agent 2 optimizes for 1-page format

## Troubleshooting

### "GEMINI_API_KEY not found"
- Check your `.env` file exists in project root
- Verify the key is on the correct line
- No spaces around the `=` sign

### PDF Generation Fails
WeasyPrint needs system libraries:

**Windows:**
- Download and install [GTK3 Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0
```

### Job Scraping Doesn't Work
- Some sites block automated access
- Use manual paste instead
- Make sure URL is accessible in your browser

## Example Session

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run app
streamlit run app.py

# Follow the UI workflow
# 1. Upload: data/resumes/sample_resume.md
# 2. Paste a job description
# 3. Click "Analyze Resume"
# 4. Review suggestions and select desired changes
# 5. Click "Apply Changes"
# 6. Review modified resume
# 7. Click "Re-score Resume"
# 8. Approve and export to PDF
```

## What's Happening Behind the Scenes?

1. **Agent 1** (Scorer): Analyzes your resume using Gemini AI, compares it to the job description, and generates targeted suggestions

2. **Agent 2** (Modifier): Takes your selected suggestions and intelligently rewrites your resume while keeping it concise and relevant

3. **Agent 3** (Re-scorer): Evaluates the improvements, provides before/after comparison, and recommends approval

4. **PDF Exporter**: Converts the final markdown resume to a professionally formatted PDF

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [CLAUDE.md](CLAUDE.md) for architecture details
- Customize prompts in agent files for your specific needs
- Extend the system with additional features

## Need Help?

- Check the main README.md
- Open an issue on GitHub
- Review the agent code in `agents/` directory

---

**Ready to optimize your resume? Let's go!** 🚀
