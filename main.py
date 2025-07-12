# To run: uv run streamlit run main.py --> 
# this will use streamlit to load in this Python file and render the user interface in our web browser
import streamlit as st    
import PyPDF2
import io
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# When using Streamlit:
# we can write anything onto this page, and Streamlit will automatically handle rendering it correctly

# allows us to configure the name of our tab/page (ex) like in HTML) => "Name of our website"
st.set_page_config(page_title="AI Resume Critiquer", page_icon="📄", layout="centered")

st.title("AI Resume Critiquer")
st.markdown("Upload you resume and get AI-powered feedback tailored to your needs")

# make variable below, bc we'll pass it to openai module to initialize our LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# input field
uploaded_file = st.file_uploader("Upload your resume (PDF of TXT)", type=["pdf", "txt"])
# this will give better context for our LLM
job_role = st.text_input("Enter the job role you're targetting (optional)")

analyze = st.button("Analyze Resume")

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

# try to load in our file content
if analyze:
    try:
        file_content = extract_text_from_file(uploaded_file)

        # make sure content in file (remove leading white spaces)
        if not file_content.strip():
            st.error("File does not have any content...")
            st.stop()
        
        # Create a prompt that contains the text from our PDF file, 
        # pass it to an LLM, and give it recommendations for our resume
        prompt = f"""Please analyze this resume and provide constructive feedback.
        Focus on the following aspects:
        1. Content clarity and impact
        2. Skills presentation
        3. Experience descriptions
        4. Specific improvements for {job_role if job_role else 'general job applications'}

        Resume content:
        {file_content}
        
        Please provide your analysis in a clear, structured format with specific recommendations."""

        # client for accessing OpenAI LLMs
        client = OpenAI(api_key=OPENAI_API_KEY)
        # generate response
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [
                {"role" : "system", "content": "You are an expert resume reviewer with years of experience in HR and recruitment."},
                {"role" : "user", "content": prompt} 
            ],
            temperature=0.7,
            max_tokens=1000
        )
        # print response
        st.markdown('### Analysis Results')
        # to make sure we get the first response -> choices[0], then access the message, then the content
        st.markdown(response.choices[0].message.content )

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


