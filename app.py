from PyPDF2 import PdfReader
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import numpy as np
import json
from groq import Groq

# ==========================
# CONFIG
# ==========================
st.set_page_config(page_title="AI Memory Assistant", page_icon="🧠", layout="wide")

memory_file = "student_memory.csv"
notes_file = "notes_database.csv"

# ==========================
# INIT SESSION STATE
# ==========================
if "exam_started" not in st.session_state:
    st.session_state.exam_started = False

if "exam_index" not in st.session_state:
    st.session_state.exam_index = 0

if "exam_questions" not in st.session_state:
    st.session_state.exam_questions = []

if "exam_answers" not in st.session_state:
    st.session_state.exam_answers = {}

if "quiz_scores" not in st.session_state:
    st.session_state.quiz_scores = []

# ==========================
# AI QUIZ GENERATOR
# ==========================
def generate_mcqs_with_ai(notes_text):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
You are an expert teacher.

Generate EXACTLY 5 multiple choice questions.

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
- Exactly 5 questions
- answer must be A/B/C/D only
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
    st.info("Google-Forms Style Exam Mode + AI Quiz System")

# ==========================
# UPLOAD NOTES
# ==========================
elif menu == "📄 Upload Notes":

    st.title("📄 Upload Notes")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    extracted_text = ""

    if uploaded_file:
        pdf = PdfReader(uploaded_file)

        for page in pdf.pages:
            extracted_text += page.extract_text() or ""

        st.success("PDF Extracted!")

        st.text_area("Preview", extracted_text[:3000], height=200)

        topic = st.text_input("Topic Name")

        if st.button("Save Notes") and topic:

            db = pd.read_csv(notes_file) if os.path.exists(notes_file) else pd.DataFrame(columns=["Topic", "Notes"])

            db.loc[len(db)] = [topic, extracted_text]
            db.to_csv(notes_file, index=False)

            st.success("Saved!")

# ==========================
# GENERATE QUIZ
# ==========================
elif menu == "🤖 Generate Quiz":

    st.title("🤖 Generate Quiz")

    if os.path.exists(notes_file):
        db = pd.read_csv(notes_file)

        topic = st.selectbox("Select Topic", db["Topic"])
        notes_text = db[db["Topic"] == topic]["Notes"].values[0]

        if st.button("Generate Quiz Cards"):

            raw = generate_mcqs_with_ai(notes_text)
            questions = parse_mcqs(raw)

            st.session_state.exam_questions = questions
            st.session_state.exam_index = 0
            st.session_state.exam_answers = {}
            st.session_state.exam_started = True

            st.success("Quiz Ready! Go to Exam Mode")

# ==========================
# EXAM MODE (GOOGLE FORM STYLE)
# ==========================
elif menu == "🧠 Exam Mode":

    st.title("🧠 Exam Mode (Google Forms Style)")

    questions = st.session_state.exam_questions

    if not questions:
        st.warning("Generate quiz first!")
        st.stop()

    idx = st.session_state.exam_index
    q = questions[idx]

    progress = (idx + 1) / len(questions)
    st.progress(progress)

    st.markdown(f"### Question {idx+1} / {len(questions)}")
    st.subheader(q["question"])

    choice = st.radio("Select answer:", q["options"], key=idx)

    col1, col2, col3 = st.columns(3)

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

    with col3:
        st.write("")

# ==========================
# RESULT PAGE
# ==========================
if st.session_state.get("exam_finished", False):

    st.title("🎯 Exam Result")

    questions = st.session_state.exam_questions
    answers = st.session_state.exam_answers

    score = 0

    for i, q in enumerate(questions):

        correct_index = ["A", "B", "C", "D"].index(q["answer"])
        correct = q["options"][correct_index]

        if answers.get(i) == correct:
            score += 1

    st.success(f"Final Score: {score} / {len(questions)}")

    if st.button("Restart Exam"):
        st.session_state.clear()
        st.rerun()
