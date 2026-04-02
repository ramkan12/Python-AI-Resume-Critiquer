# AI Resume Analyzer & Optimizer

A comprehensive AI-powered tool that provides detailed resume analysis, scores, and generates an optimized version of your resume tailored to your target role.

## Features

### 1. Detailed Resume Critique
- **Overall Score (0-100)**: Get an instant assessment of your resume quality
- **Category-Specific Scores**:
  - Content Quality
  - Formatting
  - ATS Optimization
  - Impact Quantification
  - Keyword Relevance
- **Strengths Analysis**: Understand what's working well in your resume
- **Weaknesses Identification**: Learn what needs improvement
- **Actionable Recommendations**: Get specific, prioritized suggestions for improvement
- **Missing Elements Detection**: Identify what's missing from your resume

### 2. AI-Optimized Resume Generation
- Stronger action verbs and impactful language
- Quantified achievements
- ATS-optimized keywords
- Professional formatting
- Results-oriented bullet points
- Compelling professional summary

### 3. Multiple Download Formats
- **PDF**: Professional, ready-to-send format with clean styling
- **Markdown**: Easy to edit and customize
- **Plain Text**: Universal compatibility

### 4. Before & After Comparison
- Side-by-side view of original vs optimized resume
- Easy comparison to understand improvements

### 5. Example Resume Feature
- Test the tool without uploading your own resume
- See how the analysis works with sample data

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
   - Create a `.env` file in the project directory
   - Add your API key: `OPENAI_API_KEY=your_api_key_here`

## Usage

Run the application:
```bash
streamlit run main.py
```

Or with uv:
```bash
uv run streamlit run main.py
```

The application will open in your default web browser.

## How to Use

1. **Upload Your Resume**: Upload a PDF or TXT file of your current resume
   - Alternatively, use the "Use Example Resume" button to test with sample data

2. **Specify Target Role** (Optional): Enter the job role you're targeting for better optimization

3. **Analyze & Optimize**: Click the "Analyze & Optimize Resume" button

4. **Review Your Results**:
   - Check your overall score and category breakdowns
   - Read the detailed strengths and weaknesses
   - Review actionable recommendations
   - See your optimized resume

5. **Download**: Choose your preferred format (PDF, Markdown, or TXT)

6. **Compare**: Use the Before & After comparison to see what changed

## What's New (Major Improvements)

### From Previous Version

#### Fixed Issues:
- **Markdown Rendering**: Resume now displays properly formatted instead of showing raw markdown syntax
- **PDF Generation**: Completely rewritten PDF engine with professional styling and proper formatting
- **Layout**: Changed from cramped single-column to spacious wide layout

#### New Features:
- **Actual Critique Functionality**: Now provides detailed scores and feedback (previously just generated a new resume)
- **Scoring System**: 0-100 scoring across multiple categories
- **Visual Feedback**: Color-coded score cards, organized sections with custom styling
- **Specific Recommendations**: Prioritized, actionable suggestions for improvement
- **Example Resume**: Test without uploading your own resume
- **Better Organization**: Tabbed interface separating analysis from instructions
- **Side-by-Side Comparison**: Easy before/after comparison

#### Technical Improvements:
- Enhanced PDF generation with proper text parsing and styling
- Better markdown cleanup for all download formats
- Improved error handling
- Wider layout for better readability
- Custom CSS for professional appearance
- JSON-based structured analysis from AI

## Requirements

- Python 3.8+
- streamlit
- PyPDF2
- python-dotenv
- openai
- reportlab

## API Usage

This tool uses OpenAI's GPT-4o-mini model. Each analysis requires two API calls:
1. Resume critique and scoring
2. Optimized resume generation

## Tips for Best Results

- Upload a complete resume with all sections
- Specify your target job role for better optimization
- Review the AI suggestions carefully before applying them
- Customize the optimized resume further based on specific job postings
- Use the feedback to improve your resume writing skills

## Privacy

Your resume data is:
- Sent to OpenAI's API for analysis and optimization
- Not stored permanently on any server
- Processed in-memory during your session
- Deleted when you close the browser

Make sure you trust OpenAI's data handling policies before uploading sensitive information.

## License

MIT License - feel free to use and modify as needed

## Support

For issues or questions, please open an issue in the GitHub repository.
