from PyPDF2 import PdfReader
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from groq import Groq

# ==========================
# CONFIG
# ==========================
st.set_page_config(page_title="AI Memory Assistant", page_icon="🧠", layout="wide")

# ==========================
# FILES
# ==========================
notes_file = "notes_database.csv"

if not os.path.exists(notes_file):
    pd.DataFrame(columns=["Topic", "Notes"]).to_csv(notes_file, index=False)

# ==========================
# SESSION STATE INIT
# ==========================
if "exam_questions" not in st.session_state:
    st.session_state.exam_questions = []

if "exam_index" not in st.session_state:
    st.session_state.exam_index = 0

if "exam_answers" not in st.session_state:
    st.session_state.exam_answers = {}

if "exam_finished" not in st.session_state:
    st.session_state.exam_finished = False

# ==========================
# AI QUIZ GENERATOR
# ==========================
def generate_mcqs_with_ai(notes_text):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
You are an expert teacher.

Generate EXACTLY 5 multiple-choice questions.

Return ONLY valid JSON:

{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["A", "B", "C", "D"],
      "answer": "A"
    }}
  ]
}}

Rules:
- exactly 5 questions
- answer must be A/B/C/D
- no explanation

Notes:
{notes_text[:3000]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


def parse_mcqs(raw):
    try:
        return json.loads(raw)["questions"]
    except:
        return []

# ==========================
# SIDEBAR
# ==========================
menu = st.sidebar.radio("Navigation", [
    "🏠 Home",
    "📄 Upload Notes",
    "🤖 Generate Quiz",
    "🧠 Exam Mode"
])

# ==========================
# HOME
# ==========================
if menu == "🏠 Home":
    st.title("🧠 AI Memory Assistant")
    st.markdown("### AI Powered Learning + Exam System")
    st.info("Upload notes → Generate quiz → Take exam mode like Google Forms")

# ==========================
# UPLOAD NOTES
# ==========================
elif menu == "📄 Upload Notes":

    st.title("📄 Upload Notes (PDF)")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    extracted_text = ""

    if uploaded_file:
        pdf = PdfReader(uploaded_file)

        for page in pdf.pages:
            extracted_text += page.extract_text() or ""

        st.success("PDF Extracted")

        st.text_area("Preview", extracted_text[:3000], height=200)

        topic = st.text_input("Topic Name")

        if st.button("Save Notes") and topic:

            db = pd.read_csv(notes_file)

            new_row = {
                "Topic": topic,
                "Notes": extracted_text
            }

            db.loc[len(db)] = new_row
            db.to_csv(notes_file, index=False)

            st.success("Saved Successfully")

# ==========================
# GENERATE QUIZ
# ==========================
elif menu == "🤖 Generate Quiz":

    st.title("🤖 AI Quiz Generator")

    db = pd.read_csv(notes_file)

    if len(db) == 0:
        st.warning("No notes found")
    else:

        topic = st.selectbox("Select Topic", db["Topic"])
        notes_text = db[db["Topic"] == topic]["Notes"].values[0]

        if st.button("Generate Quiz"):

            raw = generate_mcqs_with_ai(notes_text)
            questions = parse_mcqs(raw)

            if not questions:
                st.error("AI failed to generate quiz")
            else:
                st.session_state.exam_questions = questions
                st.session_state.exam_index = 0
                st.session_state.exam_answers = {}
                st.session_state.exam_finished = False

                st.success("Quiz Generated! Go to Exam Mode")

# ==========================
# EXAM MODE (GOOGLE FORM STYLE)
# ==========================
elif menu == "🧠 Exam Mode":

    st.title("🧠 Exam Mode (Google Forms Style)")

    questions = st.session_state.exam_questions

    if not questions:
        st.warning("Please generate quiz first")
        st.stop()

    idx = st.session_state.exam_index
    q = questions[idx]

    # progress bar
    st.progress((idx + 1) / len(questions))

    st.markdown(f"### Question {idx+1} / {len(questions)}")
    st.subheader(q["question"])

    choice = st.radio("Select answer:", q["options"], key=f"q_{idx}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Previous") and idx > 0:
            st.session_state.exam_index -= 1
            st.rerun()

    with col2:
        if st.button("Save & Next ➡"):

            st.session_state.exam_answers[idx] = choice

            if idx < len(questions) - 1:
                st.session_state.exam_index += 1
                st.rerun()
            else:
                st.session_state.exam_finished = True
                st.rerun()

# ==========================
# RESULT PAGE
# ==========================
if st.session_state.get("exam_finished", False):

    st.title("🎯 Final Result")

    questions = st.session_state.exam_questions
    answers = st.session_state.exam_answers

    score = 0

    for i, q in enumerate(questions):

        correct_index = ["A", "B", "C", "D"].index(q["answer"])
        correct = q["options"][correct_index]

        if answers.get(i) == correct:
            score += 1

    st.success(f"Your Score: {score} / {len(questions)}")

    if st.button("Restart Exam"):
        st.session_state.clear()
        st.rerun()
