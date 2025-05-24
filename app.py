import streamlit as st
import fitz  
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import google.generativeai as genai


st.title("Authentication")
if not st.experimental_user.is_logged_in:
    if st.button("Authenticate"):
        st.login("auth0")

st.json(st.experimental_user)
st.header(f"Hello{st.experimental_user.name}")
st.image{st.experimental_user.picture}

def create_qr_code(data):
    """Generate a QR code image for the given data."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,  # Reduced box size for smaller QR code
        border=2,    # Reduced border for compact size
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def save_summary_to_pdf(summary):
    """Save the summary text to a PDF file."""
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    # Add summary text to the PDF
    c.drawString(50, height - 50, "Medical Report Summary:")
    text = c.beginText(50, height - 70)
    text.setFont("Helvetica", 10)
    text.setTextOrigin(50, height - 70)
    text.setLeading(14)

    for line in summary.split("\n"):
        text.textLine(line)

    c.drawText(text)
    c.showPage()
    c.save()

    pdf_buffer.seek(0)
    return pdf_buffer



api_key = st.secrets["gcp"]["gemini_api_key"]
genai.configure(api_key=api_key)


generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",
    generation_config=generation_config,
)

chat_session = model.start_chat(
    history=[
        {
            "role": "user",
            "parts": [
                "You are a medical expert. Analyze the medical reports I send and provide a concise, layperson-friendly summary highlighting key medical information, tests, diagnoses, and recommended actions which should not be below bullet points. Avoid mentioning doctors' names, but mention the required medical specialties if relevant. Translate the summary into the selected language for better comprehension.Highlight key medical information, tests, diagnoses, and actions in few bullet points along with Interpretation and recommendation all in 110 words. Avoid mentioning any doctor's name. If necessary, include the relevant medical specialties for the case and if any values present please include that in the summary. \n",
            ],
        },
        {
            "role": "model",
            "parts": [
                "Okay, I understand. Please send me the medical reports. I will analyze them and provide you with:\n\n*   A concise, layperson-friendly summary.\n*   Key medical information, tests, and diagnoses in bullet points.\n*   Recommended actions in bullet points.\n*   Mention of relevant medical specialties if needed (e.g., cardiology, neurology).\n*   Translation of the summary into your chosen language for better comprehension.\n*  Include values present in the summary if necessary.\n\nI will ensure the summary is approximately 110 words or less and avoids mentioning any doctor's names. I will include Interpretation and recommendation all within the summarized output. I'm ready when you are!\n",
            ],
        },
    ]
)


st.title("MedBrief-AI:Medical Report Summarizer")


uploaded_file = st.file_uploader("Upload a Medical Report (PDF)", type="pdf")


language_options = {
    "English": "en",
    "Hindi": "hi",
    "Punjabi": "pa",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Bengali": "bn",
}
selected_language = st.selectbox("Select the output language", options=language_options.keys())


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
        st.text_area("Extracted Text", extracted_text, height=150)

        
        with st.spinner("Analyzing the report..."):
            prompt = f"""
            Summarize the following medical report in {selected_language} language. 
            Highlight key medical information, tests, diagnoses, and actions in few bullet points along with Interpretation and recommendation all in 110 words. Avoid mentioning any doctor's name. 
            If necessary, include the relevant medical specialties for the case and if any values present please include that in the summary. 

            Report: {extracted_text}
            """
            response = chat_session.send_message(prompt)
            summary = response.text

        
        st.subheader("Summary")
        st.write(summary)

        
        qr_buffer = create_qr_code(summary)
        st.subheader("QR Code")
        st.image(qr_buffer, caption="Scan to view the summary")

        
        pdf_buffer = save_summary_to_pdf(summary)
        st.download_button(
            label="Download Summary as PDF",
            data=pdf_buffer,
            file_name="medical_summary.pdf",
            mime="application/pdf",
        )
