import streamlit as st
import openai
import PyPDF2
import docx
import io
import tempfile
import datetime
import os

def read_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
    text = ''
    for page in reader.pages:
        text += page.extract_text() + '\n'
    return text

def read_docx(uploaded_file):
    doc = docx.Document(io.BytesIO(uploaded_file.read()))
    text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    return text

def generate_questions_and_answers(api_key, text, num_comprehension, num_why, num_how, model):
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": "You are an assistant who provides precise and informative answers."},
                      {"role": "user", "content": f"Create {num_comprehension} comprehension questions, {num_why} 'why' questions, and {num_how} 'how' questions along with their answers based on this text: {text}"}]
        )
        return response.choices[0].message['content']
    except openai.error.InvalidRequestError as e:
        print("Error: ", e)
        return ""

def split_into_sections(text, max_length=4000):
    sections = []
    words = text.split()
    current_section = ""
    for word in words:
        if len(current_section) + len(word) < max_length:
            current_section += word + " "
        else:
            sections.append(current_section)
            current_section = word + " "
    if current_section:
        sections.append(current_section)
    return sections

def main():
    st.title("💬 Question-Answer Generator")
    st.write("For each uploaded file, the app creates a specified number of comprehension, 'why', and 'how' questions along with the answers.")
    st.write("Generating the questions takes some time, depending on the number and size of the file(s) ⏳.")

    # Sidebar für die Eingabe der Fragenanzahl
    with st.sidebar:
        api_key = st.text_input("Enter your OpenAI API Key", type="password")
        num_comprehension = st.number_input("Number of comprehension questions", min_value=1, value=2)
        num_why = st.number_input("Number of 'why' questions", min_value=1, value=2)
        num_how = st.number_input("Number of 'how' questions", min_value=1, value=2)
        model_choice = st.selectbox("Choose the AI model", ["gpt-4", "gpt-3.5-turbo-16k"])

    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True, type=['txt', 'pdf', 'docx'])

    if st.button("Generate questions"):
        if uploaded_files and api_key:
            current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            warning_notice = (
                "WARNING! Please note that the following questions and answers were generated with the support "
                "of Artificial Intelligence (AI). Despite the constant striving for precision and reliability, "
                "the answers may contain errors or inaccuracies. "
                f"It is recommended to verify the provided information with further research if needed. ({current_timestamp})\n\n"
            )
            entire_content = warning_notice

            for uploaded_file in uploaded_files:
                file_title = os.path.splitext(uploaded_file.name)[0]
                entire_content += f"\nFILE TITLE: {file_title}\n\n"

                if uploaded_file.type == "text/plain":
                    text = str(uploaded_file.read(), "utf-8")
                elif uploaded_file.type == "application/pdf":
                    text = read_pdf(uploaded_file)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    text = read_docx(uploaded_file)

                if text:
                    sections = split_into_sections(text)
                    for section in sections:
                        questions_and_answers = generate_questions_and_answers(api_key, section, num_comprehension, num_why, num_how, model_choice)
                        entire_content += questions_and_answers + "\n\n<- - - - - - - - - ->\n\n"

            file_name = f"AI-Questions-{datetime.datetime.now().strftime('%Y-%m-%d')}.txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w') as fp:
                fp.write(entire_content)
                download_fn = fp.name

            with open(download_fn, "r") as file:
                st.download_button(
                    label="Download questions",
                    data=file,
                    file_name=file_name,
                    mime="text/plain"
                )

            #st.success("Questions successfully generated.")

if __name__ == "__main__":
    main()
