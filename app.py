import streamlit as st
import fitz  
import google.generativeai as genai


genai.configure(api_key='AIzaSyAZBLckLuAB')


generation_config = {
    "temperature": 0.7,
    "top_p": 0.90,
    "top_k": 500,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-Pro-Advanced",
    generation_config=generation_config,
)

chat_session = model.start_chat(
    history=[
        {
            "role": "user",
            "parts": [
                "You are a medical expert. Analyze the medical reports I send and provide a concise, layperson-friendly summary highlighting key medical information, tests, diagnoses, and recommended actions. Avoid retaining information from previous reports, as each report is unique, and please provide the final in bullet points"
            ],
        },
        {
            "role": "model",
            "parts": [
                "Understood. Please send me the medical reports one at a time. I will analyze each report and provide a clear and concise summary."
            ],
        },
    ]
)


st.title("Medical Report Summarizer")


uploaded_file = st.file_uploader("Upload a Medical Report (PDF)", type="pdf")


def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text += page.get_text()
    pdf_document.close()
    return text


if uploaded_file:
    if st.button("Analyze"):
        
        extracted_text = extract_text_from_pdf(uploaded_file)
        st.text_area("Extracted Text", extracted_text, height=300)

        
        with st.spinner("Analyzing the report..."):
            response = chat_session.send_message(extracted_text)
            summary = response.text

        
        st.subheader("Summary")
        st.write(summary)
