# To run: uv run streamlit run main.py -->
# this will use streamlit to load in this Python file and render the user interface in our web browser
import streamlit as st
import PyPDF2
import io
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import re
import json

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

load_dotenv()

# allows us to configure the name of our tab/page (ex) like in HTML) => "Name of our website"
st.set_page_config(page_title="AI Resume Analyzer & Optimizer", page_icon="📄", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #f0f0f0;
        margin: 0.5rem 0 0 0;
    }
    .score-card {
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    .score-high {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .score-medium {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    .score-low {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
    }
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .improvement-box {
        background: #e8f4f8;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        color: #1a1a1a;
    }
    .strength-box {
        background: #e8f5e9;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        color: #1a1a1a;
    }
    .warning-box {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        color: #1a1a1a;
    }
    .category-bar-container {
        margin: 1rem 0;
        padding: 0.75rem;
        background: #1e1e1e;
        border-radius: 8px;
    }
    .category-bar-row {
        display: flex;
        align-items: center;
        margin: 0.8rem 0;
        gap: 1rem;
    }
    .category-label {
        min-width: 120px;
        font-weight: 600;
        font-size: 0.95rem;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .category-bar-wrapper {
        flex: 1;
        background: #2a2a2a;
        border-radius: 8px;
        height: 32px;
        position: relative;
        overflow: hidden;
    }
    .category-bar-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.6s ease;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 10px;
        font-weight: bold;
        font-size: 0.9rem;
        color: white;
    }
    .bar-score-low {
        background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
    }
    .bar-score-medium {
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
    }
    .bar-score-high {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
    }
    .category-score-text {
        min-width: 60px;
        text-align: right;
        font-weight: bold;
        font-size: 1rem;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📄 AI Resume Analyzer & Optimizer</h1>
    <p>Get detailed feedback, scores, and an AI-optimized version of your resume</p>
</div>
""", unsafe_allow_html=True)

# make variable below, bc we'll pass it to openai module to initialize our LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Tabs for different modes
tab1, tab2 = st.tabs(["📊 Analyze & Optimize Resume", "📚 How It Works"])

with tab2:
    st.markdown("""
    ### How This Tool Works

    This AI-powered tool provides comprehensive resume analysis and optimization:

    #### 1. **Detailed Critique**
    - Overall score (0-100)
    - Category-specific scores (Content, Formatting, ATS Optimization, Impact)
    - Specific strengths and areas for improvement
    - Actionable recommendations

    #### 2. **Optimized Version**
    - AI-enhanced resume with stronger action verbs
    - Quantified achievements
    - ATS-optimized keywords
    - Professional formatting
    - Download as PDF, Markdown, or TXT

    #### 3. **Side-by-Side Comparison**
    - See your original resume
    - Compare with the optimized version
    - Understand what changed and why

    ### Tips for Best Results
    - Upload a complete resume with all sections
    - Specify your target job role for better optimization
    - Review the feedback carefully before downloading
    - Customize further based on specific job postings
    """)

    st.markdown("---")
    st.markdown("### Need a Resume to Test?")
    if st.button("Use Example Resume"):
        st.session_state['use_example'] = True
        st.rerun()

with tab1:
    # Check if we should use example
    use_example = st.session_state.get('use_example', False)

    col_upload, col_input = st.columns([2, 1])

    with col_upload:
        if not use_example:
            uploaded_file = st.file_uploader("Upload your current resume (PDF or TXT)", type=["pdf", "txt"])
        else:
            st.info("Using example resume. Upload your own to analyze it instead.")
            uploaded_file = None
            if st.button("Clear Example"):
                st.session_state['use_example'] = False
                st.rerun()

    with col_input:
        job_role = st.text_input("Target job role (optional)", placeholder="e.g., Software Engineer")

    analyze_button = st.button("Analyze & Optimize Resume", type="primary", use_container_width=True)

# function that will extract the text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

# function to clean up PDF text for better display
def clean_pdf_text_for_display(text):
    """Clean up PDF-extracted text that has words on separate lines"""
    import re

    # Simply join all text with spaces, removing ALL newlines
    text = text.replace('\n', ' ')

    # Clean up multiple spaces
    text = re.sub(r' +', ' ', text)

    # Add newlines before common section headers
    section_headers = ['SUMMARY', 'EDUCATION', 'EXPERIENCE', 'PROJECTS', 'SKILLS',
                       'CERTIFICATIONS', 'AWARDS', 'LANGUAGES', 'OBJECTIVE']
    for header in section_headers:
        text = text.replace(f' {header} ', f'\n\n{header}\n')

    # Add line breaks before bullet points
    text = text.replace(' ● ', '\n● ')

    # Add line breaks before common date patterns (e.g., "May 2025", "2020 - 2023")
    text = re.sub(r' ((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4})', r'\n\1', text)
    text = re.sub(r' (\d{4} - \d{4})', r'\n\1', text)

    # Clean up any triple+ newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

# function to load in content
def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        # taking uploaded file, reading it in, converting it into byte object:
        # which will be able to be loaded by pdf reader, then extracting texts from it here
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    # if not pdf, must be text file, which will read and decode as utf-8
    return uploaded_file.read().decode("utf-8")

def get_example_resume():
    """Return an example resume for testing"""
    return """John Smith
    Tampa, FL
    john.smith@email.com | 555-123-4567
    linkedin.com/in/johnsmith

    OBJECTIVE
    Looking for a software engineering position where I can use my skills.

    EDUCATION
    University of South Florida
    Bachelor of Science in Computer Science
    GPA: 3.5

    EXPERIENCE
    Tech Company - Software Developer
    2022 - Present
    - Worked on various projects
    - Used Python and JavaScript
    - Collaborated with team members
    - Fixed bugs

    Startup Inc - Intern
    Summer 2021
    - Helped with development tasks
    - Learned new technologies
    - Attended meetings

    SKILLS
    Python, JavaScript, React, SQL, Git
    """

def analyze_resume(resume_text, target_role=""):
    """Get detailed critique and analysis of the resume"""
    client = OpenAI(api_key=OPENAI_API_KEY)

    critique_prompt = f"""You are an expert resume reviewer and career coach. Analyze this resume and provide a detailed critique.

Target Role: {target_role if target_role else 'General professional positions'}

Resume Content:
{resume_text}

Provide your analysis in the following JSON format:
{{
    "overall_score": <number 0-100>,
    "category_scores": {{
        "content_quality": <number 0-100>,
        "formatting": <number 0-100>,
        "ats_optimization": <number 0-100>,
        "impact_quantification": <number 0-100>,
        "keyword_relevance": <number 0-100>
    }},
    "strengths": [
        "<specific strength 1>",
        "<specific strength 2>",
        "<specific strength 3>"
    ],
    "weaknesses": [
        "<specific weakness 1>",
        "<specific weakness 2>",
        "<specific weakness 3>"
    ],
    "improvements": [
        {{
            "issue": "<specific issue>",
            "suggestion": "<actionable fix>",
            "priority": "<high/medium/low>"
        }}
    ],
    "missing_elements": ["<element 1>", "<element 2>"],
    "summary": "<2-3 sentence overall assessment>"
}}

Be specific and actionable in your feedback."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert resume reviewer with 15+ years of experience in recruiting and career coaching. Provide honest, detailed, and actionable feedback. Return ONLY valid JSON."},
            {"role": "user", "content": critique_prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )

    # Parse the JSON response
    try:
        critique_data = json.loads(response.choices[0].message.content)
        return critique_data
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "overall_score": 70,
            "category_scores": {
                "content_quality": 70,
                "formatting": 65,
                "ats_optimization": 60,
                "impact_quantification": 55,
                "keyword_relevance": 60
            },
            "strengths": ["Resume structure is clear", "Education is well presented"],
            "weaknesses": ["Lacks quantified achievements", "Could use stronger action verbs"],
            "improvements": [
                {
                    "issue": "Generic objective statement",
                    "suggestion": "Replace with a compelling professional summary highlighting key achievements",
                    "priority": "high"
                }
            ],
            "missing_elements": ["Professional summary", "Quantified metrics"],
            "summary": "Your resume has a solid foundation but needs enhancement in impact and specificity."
        }

def generate_improved_resume(resume_text, target_role=""):
    """Generate an improved version of the resume"""
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""You are an expert resume writer and career coach. Create a significantly improved version of this resume that will stand out to recruiters.

Job Role Target: {target_role if target_role else 'General professional positions'}

Instructions:
1. Replace objective with a powerful professional summary
2. Use strong action verbs (Led, Engineered, Implemented, Optimized, etc.)
3. Add quantified achievements wherever possible
4. Optimize for ATS with relevant keywords
5. Improve formatting and structure
6. Make bullet points results-oriented and impactful
7. Ensure consistency in formatting

Current Resume:
{resume_text}

Provide the complete improved resume in clean, professional markdown format. Use proper headers (##) for sections. Make it compelling and achievement-focused. DO NOT include code blocks or triple backticks in your response - just clean markdown."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert resume writer with 10+ years of experience. Create compelling, ATS-optimized resumes. Return clean markdown without code blocks."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2500
    )

    return response.choices[0].message.content.strip()

def create_downloadable_resume(improved_resume_text, name="Resume"):
    """Create a downloadable text file of the improved resume"""
    # Add header with generation info
    header = f"# Improved Resume - Generated on {datetime.now().strftime('%B %d, %Y')}\n\n"
    full_content = header + improved_resume_text
    
    return full_content.encode('utf-8')

def create_pdf_resume(improved_resume_text):
    """Create a professional PDF version of the improved resume"""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab library is required for PDF generation")

    buffer = io.BytesIO()

    # Create the PDF document with professional margins
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=0.75*inch, leftMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)

    # Get styles
    styles = getSampleStyleSheet()

    # Create professional resume styles
    name_style = ParagraphStyle(
        'Name',
        parent=styles['Normal'],
        fontSize=24,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a1a1a'),
        fontName='Helvetica-Bold',
        leading=28
    )

    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=3,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#444444'),
        leading=14
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontSize=13,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.HexColor('#1a1a1a'),
        fontName='Helvetica-Bold',
        leading=16,
        borderWidth=0,
        borderPadding=0,
        borderColor=colors.HexColor('#cccccc'),
        keepWithNext=True
    )

    subsection_style = ParagraphStyle(
        'SubSection',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=2,
        spaceBefore=6,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#2a2a2a'),
        leading=14
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=3,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#333333')
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=2,
        leftIndent=20,
        bulletIndent=10,
        leading=13,
        textColor=colors.HexColor('#333333')
    )

    # Parse the resume content
    story = []

    # Remove markdown code blocks if present
    improved_resume_text = re.sub(r'```[\w]*\n?', '', improved_resume_text)

    lines = improved_resume_text.split('\n')

    # Track what we're parsing
    parsing_header = True
    header_lines = []

    for i, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines in most cases
        if not line:
            if not parsing_header and story:
                story.append(Spacer(1, 0.05*inch))
            continue

        # Skip markdown separators
        if line == '---' or line.startswith('```'):
            continue

        # Handle headers
        if line.startswith('# ') and not line.startswith('## '):
            # Main title (name)
            name_text = line[2:].strip()
            story.append(Paragraph(name_text, name_style))
            parsing_header = True
            continue

        # Handle section headers (## Section)
        if line.startswith('## '):
            parsing_header = False
            section_title = line[3:].strip().upper()
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(section_title, section_style))
            # Add a line under section
            story.append(Spacer(1, 0.02*inch))
            continue

        # Handle subsection headers (### Subsection)
        if line.startswith('### '):
            parsing_header = False
            subsection_title = line[4:].strip()
            # Clean markdown formatting
            subsection_title = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', subsection_title)
            subsection_title = re.sub(r'\*(.*?)\*', r'<i>\1</i>', subsection_title)
            story.append(Paragraph(subsection_title, subsection_style))
            continue

        # If still in header (contact info section)
        if parsing_header and not line.startswith('#'):
            # Clean up contact line
            clean_line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
            # Remove markdown formatting
            clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_line)
            clean_line = re.sub(r'\*(.*?)\*', r'\1', clean_line)
            story.append(Paragraph(clean_line, contact_style))
            continue

        # Handle bullet points
        if line.startswith(('• ', '- ', '* ')):
            parsing_header = False
            # Get bullet text
            if line.startswith('• '):
                bullet_text = line[2:].strip()
            else:
                bullet_text = line[2:].strip()

            # Clean markdown formatting
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            bullet_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', bullet_text)
            bullet_text = re.sub(r'__(.*?)__', r'<b>\1</b>', bullet_text)
            bullet_text = re.sub(r'_(.*?)_', r'<i>\1</i>', bullet_text)
            bullet_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', bullet_text)

            story.append(Paragraph(f"• {bullet_text}", bullet_style))
            continue

        # Handle regular content lines
        if line and not line.startswith('#'):
            parsing_header = False
            # Clean markdown formatting
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            clean_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean_text)
            clean_text = re.sub(r'__(.*?)__', r'<b>\1</b>', clean_text)
            clean_text = re.sub(r'_(.*?)_', r'<i>\1</i>', clean_text)
            clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)

            # Detect if this is a job title/date line (usually has dates or location)
            if re.search(r'(20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\||Remote)', clean_text):
                story.append(Paragraph(clean_text, subsection_style))
            else:
                story.append(Paragraph(clean_text, body_style))

    # Build the PDF
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        # If PDF generation fails, raise with details
        raise Exception(f"PDF generation failed: {str(e)}")

# Main analysis logic
if analyze_button:
    # Get resume content
    is_pdf = False
    if use_example:
        file_content = get_example_resume()
    elif uploaded_file:
        try:
            file_content = extract_text_from_file(uploaded_file)
            is_pdf = uploaded_file.type == "application/pdf"
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.stop()
    else:
        st.error("Please upload a resume or use the example resume!")
        st.stop()

    # Validate content
    if not file_content.strip():
        st.error("The resume appears to be empty. Please upload a valid resume.")
        st.stop()

    try:
        # Step 1: Analyze the resume
        with st.spinner("🔍 Analyzing your resume..."):
            critique = analyze_resume(file_content, job_role)

        # Step 2: Generate improved version
        with st.spinner("✨ Creating optimized version..."):
            improved_resume = generate_improved_resume(file_content, job_role)

        # Display results
        st.markdown("---")

        # CRITIQUE SECTION
        st.markdown("## 📊 Resume Analysis")

        # Overall score with colored card
        score = critique.get('overall_score', 70)
        score_class = 'score-high' if score >= 80 else 'score-medium' if score >= 60 else 'score-low'

        st.markdown(f"""
        <div class="score-card {score_class}">
            <h2 style="margin: 0; font-size: 3rem;">{score}/100</h2>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem;">Overall Score</p>
        </div>
        """, unsafe_allow_html=True)

        # Category scores
        st.markdown("### Category Breakdown")
        cat_scores = critique.get('category_scores', {})

        categories = [
            ('content_quality', 'Content', '📝'),
            ('formatting', 'Format', '🎨'),
            ('ats_optimization', 'ATS', '🤖'),
            ('impact_quantification', 'Impact', '📈'),
            ('keyword_relevance', 'Keywords', '🔑')
        ]

        # Build HTML for horizontal bar chart
        bars_html = '<div class="category-bar-container">'
        for key, label, icon in categories:
            value = cat_scores.get(key, 70)
            # Determine color class based on score
            if value >= 80:
                bar_class = 'bar-score-high'
            elif value >= 60:
                bar_class = 'bar-score-medium'
            else:
                bar_class = 'bar-score-low'

            bars_html += f'<div class="category-bar-row"><div class="category-label"><span>{icon}</span><span>{label}</span></div><div class="category-bar-wrapper"><div class="category-bar-fill {bar_class}" style="width: {value}%;">{value}</div></div><div class="category-score-text">{value}/100</div></div>'
        bars_html += '</div>'

        st.markdown(bars_html, unsafe_allow_html=True)

        # Summary
        st.markdown("### Overall Assessment")
        st.info(critique.get('summary', 'Your resume shows potential but could benefit from improvements.'))

        # Two columns for strengths and weaknesses
        col_str, col_weak = st.columns(2)

        with col_str:
            st.markdown("### ✅ Strengths")
            for strength in critique.get('strengths', []):
                st.markdown(f"""
                <div class="strength-box">
                    {strength}
                </div>
                """, unsafe_allow_html=True)

        with col_weak:
            st.markdown("### ⚠️ Areas for Improvement")
            for weakness in critique.get('weaknesses', []):
                st.markdown(f"""
                <div class="warning-box">
                    {weakness}
                </div>
                """, unsafe_allow_html=True)

        # Detailed improvements
        st.markdown("### 🎯 Specific Recommendations")
        improvements = critique.get('improvements', [])

        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        improvements.sort(key=lambda x: priority_order.get(x.get('priority', 'medium'), 1))

        for imp in improvements:
            priority = imp.get('priority', 'medium')
            priority_emoji = '🔴' if priority == 'high' else '🟡' if priority == 'medium' else '🟢'

            st.markdown(f"""
            <div class="improvement-box">
                <strong>{priority_emoji} {imp.get('issue', 'Issue')}</strong><br/>
                💡 <em>{imp.get('suggestion', 'Suggestion')}</em>
            </div>
            """, unsafe_allow_html=True)

        # Missing elements
        if critique.get('missing_elements'):
            st.markdown("### 📋 Missing Elements")
            missing = critique.get('missing_elements', [])
            st.warning(f"Consider adding: {', '.join(missing)}")

        # OPTIMIZED RESUME SECTION
        st.markdown("---")
        st.markdown("## ✨ Your Optimized Resume")

        # Two columns: resume display and download options
        col_resume, col_actions = st.columns([3, 1])

        with col_resume:
            # Display the improved resume with proper markdown rendering
            st.markdown(improved_resume)

        with col_actions:
            st.markdown("### 📥 Download")

            # Create downloadable files
            resume_file = create_downloadable_resume(improved_resume)

            if REPORTLAB_AVAILABLE:
                try:
                    # Create PDF version
                    pdf_file = create_pdf_resume(improved_resume)

                    # PDF Download button (primary)
                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_file,
                        file_name=f"resume_optimized_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        help="Professional PDF ready for applications",
                        type="primary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF error: {str(e)}")
                    st.info("Using markdown download instead")

            # Markdown download
            st.download_button(
                label="📝 Markdown",
                data=resume_file,
                file_name=f"resume_optimized_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True
            )

            # Plain text download
            plain_text = re.sub(r'#{1,6}\s', '', improved_resume)
            plain_text = re.sub(r'\*\*(.+?)\*\*', r'\1', plain_text)
            plain_text = re.sub(r'\*(.+?)\*', r'\1', plain_text)

            st.download_button(
                label="📄 Plain Text",
                data=plain_text.encode('utf-8'),
                file_name=f"resume_optimized_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

            st.markdown("---")
            st.markdown("### 💡 Tips")
            st.info("✓ Review and personalize before sending")
            st.info("✓ Tailor for each job posting")

        # COMPARISON SECTION
        st.markdown("---")
        st.markdown("## 🔄 Before & After Comparison")

        tab_orig, tab_new = st.tabs(["📄 Original Resume", "✨ Optimized Resume"])

        with tab_orig:
            st.markdown("### Original Resume")
            # Clean up the display if it's from a PDF
            if is_pdf:
                display_content = clean_pdf_text_for_display(file_content)
            else:
                display_content = file_content
            # Calculate height based on content (roughly 20px per line)
            num_lines = display_content.count('\n') + 1
            calculated_height = min(max(num_lines * 20, 400), 800)  # Between 400-800px
            st.text_area("", display_content, height=calculated_height, disabled=True, label_visibility="collapsed")

        with tab_new:
            st.markdown("### Optimized Resume (Markdown)")
            st.code(improved_resume, language="markdown")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)