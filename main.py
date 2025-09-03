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

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

load_dotenv()

# allows us to configure the name of our tab/page (ex) like in HTML) => "Name of our website"
st.set_page_config(page_title="AI Resume Generator", page_icon="📄", layout="centered")

st.title("AI Resume Generator")
st.markdown("Upload your resume and get an AI-powered improved version tailored to your target role")

# make variable below, bc we'll pass it to openai module to initialize our LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# input field
uploaded_file = st.file_uploader("Upload your current resume (PDF or TXT)", type=["pdf", "txt"])
# this will give better context for our LLM
job_role = st.text_input("Enter the job role you're targeting (optional)")

generate = st.button("Generate Improved Resume")

# function that will extract the text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

# function to load in content
def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        # taking uploaded file, reading it in, converting it into byte object:
        # which will be able to be loaded by pdf reader, then extracting texts from it here
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    # if not pdf, must be text file, which will read and decode as utf-8
    return uploaded_file.read().decode("utf-8")

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
                          rightMargin=50, leftMargin=50,
                          topMargin=50, bottomMargin=50)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create professional resume styles
    name_style = ParagraphStyle(
        'Name',
        parent=styles['Title'],
        fontSize=20,
        spaceAfter=6,
        alignment=1,  # Center alignment
        textColor='#2c3e50',
        fontName='Helvetica-Bold'
    )
    
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        alignment=1,  # Center alignment
        textColor='#34495e'
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=16,
        textColor='#2c3e50',
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor='#bdc3c7',
        borderPadding=3
    )
    
    subsection_style = ParagraphStyle(
        'SubSection',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=4,
        spaceBefore=8,
        fontName='Helvetica-Bold',
        textColor='#34495e'
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leading=12
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=3,
        leftIndent=15,
        bulletIndent=5,
        leading=12
    )
    
    # Parse the resume content
    story = []
    lines = improved_resume_text.split('\n')
    
    is_first_section = True
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines and markdown artifacts
        if not line or line == '---' or line.startswith('```'):
            continue
            
        # Handle name (first non-empty line)
        if is_first_section and not line.startswith('#'):
            story.append(Paragraph(line, name_style))
            is_first_section = False
            continue
        
        # Handle contact info (lines right after name, before first section)
        if not line.startswith('#') and len(story) <= 3:
            # Clean up contact line formatting
            clean_line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)  # Remove markdown links
            story.append(Paragraph(clean_line, contact_style))
            continue
            
        # Handle section headers
        if line.startswith('## '):
            section_title = line[3:].strip()
            story.append(Paragraph(section_title.upper(), section_style))
        elif line.startswith('### '):
            subsection_title = line[4:].strip()
            story.append(Paragraph(subsection_title, subsection_style))
        # Handle bullet points
        elif line.startswith('• ') or line.startswith('- ') or line.startswith('* '):
            bullet_text = line[2:].strip()
            # Clean up markdown formatting and underscores
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            bullet_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', bullet_text)
            bullet_text = re.sub(r'_(.*?)_', r'<i>\1</i>', bullet_text)  # Remove underscores
            story.append(Paragraph(f"• {bullet_text}", bullet_style))
        # Handle regular content
        elif line and not line.startswith('#'):
            # Clean up markdown formatting and links
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            clean_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean_text)
            clean_text = re.sub(r'_(.*?)_', r'<i>\1</i>', clean_text)  # Remove underscores and make italic
            clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)
            
            # Handle job titles, dates, and locations differently
            if ' | ' in clean_text or (',' in clean_text and any(x in clean_text.lower() for x in ['fl', 'remote', '202'])):
                story.append(Paragraph(clean_text, subsection_style))
            else:
                story.append(Paragraph(clean_text, body_style))
    
    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# try to load in our file content
if generate:
    if not uploaded_file:
        st.error("Please upload your resume first!")
        st.stop()
        
    try:
        file_content = extract_text_from_file(uploaded_file)

        # make sure content in file (remove leading white spaces)
        if not file_content.strip():
            st.error("File does not have any content...")
            st.stop()
        
        # Create a prompt that will generate an improved resume
        prompt = f"""You are an expert resume writer and career coach. Based on the provided resume, create a significantly improved version that will stand out to recruiters and hiring managers.

        Job Role Target: {job_role if job_role else 'General professional positions'}

        Instructions:
        1. Rewrite the entire resume with stronger action verbs and quantified achievements
        2. Improve the formatting and structure for maximum impact
        3. Enhance the professional summary/objective section
        4. Optimize bullet points for ATS (Applicant Tracking Systems)
        5. Add relevant keywords for the target role
        6. Ensure consistency in formatting and style
        7. Make the content more compelling and results-oriented

        Current Resume Content:
        {file_content}

        Please provide the complete improved resume in a clean, professional format using markdown. Include all sections: contact info, professional summary, experience, education, skills, and any relevant projects or certifications. Make it ready for immediate use."""

        # Show loading message
        with st.spinner("Generating your improved resume..."):
            # client for accessing OpenAI LLMs
            client = OpenAI(api_key=OPENAI_API_KEY)
            # generate response
            response = client.chat.completions.create(
                model = "gpt-4o-mini",
                messages = [
                    {"role" : "system", "content": "You are an expert resume writer with 10+ years of experience helping professionals land their dream jobs. You specialize in creating ATS-optimized, compelling resumes that get results."},
                    {"role" : "user", "content": prompt} 
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
        # Get the improved resume content
        improved_resume = response.choices[0].message.content
        
        # Display the results
        st.markdown('## Your Improved Resume')
        st.markdown("---")
        
        # Create two columns for better layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Display the improved resume
            st.markdown(improved_resume)
        
        with col2:
            st.markdown("### Actions")
            
            # Create downloadable files
            resume_file = create_downloadable_resume(improved_resume)
            
            if REPORTLAB_AVAILABLE:
                try:
                    # Create PDF version
                    pdf_file = create_pdf_resume(improved_resume)
                    
                    # PDF Download button (primary)
                    st.download_button(
                        label="📄 Download as PDF",
                        data=pdf_file,
                        file_name=f"improved_resume_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        help="Download your improved resume as a PDF file",
                        type="primary"
                    )
                except Exception as e:
                    st.error(f"PDF generation failed: {str(e)}")
            else:
                st.info("📄 PDF generation requires reportlab. Install with: pip install reportlab")
            
            # Markdown download button
            st.download_button(
                label="📝 Download as Markdown",
                data=resume_file,
                file_name=f"improved_resume_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                help="Download your improved resume as a markdown file"
            )
            
            # Option to download as plain text
            plain_text_resume = improved_resume.replace('#', '').replace('*', '').replace('**', '')
            st.download_button(
                label="📄 Download as TXT",
                data=plain_text_resume.encode('utf-8'),
                file_name=f"improved_resume_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                help="Download as plain text file"
            )
            
            # Additional options
            st.markdown("### Tips")
            if REPORTLAB_AVAILABLE:
                st.info("💡 PDF format is ready for immediate job applications")
            st.info("🎯 Customize further based on specific job postings")
            
        # Show comparison section
        st.markdown("---")
        st.markdown("## Original vs Improved")
        
        col_orig, col_improved = st.columns(2)
        
        with col_orig:
            st.markdown("### Original Resume")
            with st.expander("Click to view original"):
                st.text(file_content[:1000] + "..." if len(file_content) > 1000 else file_content)
        
        with col_improved:
            st.markdown("### Key Improvements Made")
            st.success("✅ Enhanced with stronger action verbs")
            st.success("✅ Added quantified achievements")
            st.success("✅ Improved ATS optimization")
            st.success("✅ Better formatting and structure")
            st.success("✅ Role-specific keywords added")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Add footer with instructions
st.markdown("---")
st.markdown("### How to Use Your New Resume")
st.markdown("""
1. **Download** your improved resume using the buttons above
2. **Review** and customize any specific details for your target companies
3. **Convert** to PDF using Google Docs, Word, or an online converter (if PDF download unavailable)
4. **Tailor** further for specific job applications by adding relevant keywords
5. **Proofread** one final time before submitting
""")

st.markdown("### Need Further Customization?")
st.info("💼 For best results, customize the resume further for each specific job application by incorporating keywords from the job posting.")

if not REPORTLAB_AVAILABLE:
    st.markdown("### Install PDF Support")
    st.code("pip install reportlab", language="bash")
    st.markdown("Run the above command to enable PDF downloads.")