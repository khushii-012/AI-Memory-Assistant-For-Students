from PyPDF2 import PdfReader
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime
from groq import Groq

# ✅ SESSION STATE INITIALIZATION
if "exam_active" not in st.session_state:
    st.session_state.exam_active = False

if "questions" not in st.session_state:
    st.session_state.questions = []

if "index" not in st.session_state:
    st.session_state.index = 0

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "score" not in st.session_state:
    st.session_state.score = 0

# ==========================
# CONFIG
# ==========================
st.set_page_config(
    page_title="NeuroLearn AI",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
    .main {
        background-color: #0f1117;
    }
    h1 {
        color: #00ffcc;
        text-align: center;
    }
    .stButton>button {
        background-color: #00ffcc;
        color: black;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# FILES
# ==========================
notes_file = "notes.csv"
leaderboard_file = "leaderboard.csv"

if not os.path.exists(notes_file):
    pd.DataFrame(columns=["Topic", "Notes"]).to_csv(notes_file, index=False)

if not os.path.exists(leaderboard_file):
    pd.DataFrame(columns=["Name", "Score", "Difficulty", "Topic", "Date"]).to_csv(leaderboard_file, index=False)

# ==========================
# SESSION STATE
# ==========================
for key in ["questions", "index", "answers", "score", "start_time", "time_limit", "exam_active"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["start_time", "time_limit"] else 0

st.session_state.answers = st.session_state.answers or {}

# ==========================
# AI ENGINE
# ==========================
def generate_mcqs(notes, difficulty):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
You are a strict exam creator.

Generate 5 MCQs.

Difficulty: {difficulty}

Return ONLY JSON:

{{
 "questions": [
  {{
   "question": "...",
   "options": ["A","B","C","D"],
   "answer": "A"
  }}
 ]
}}

Notes:
{notes[:3000]}
"""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    try:
        return json.loads(res.choices[0].message.content)["questions"]
    except:
        return []

# ==========================
# UI LANDING PAGE
# ==========================
st.markdown("""
# 🧠 NeuroLearn AI

### 🚀 Turn Your Notes Into Smart Exams

💡 Upload Notes → AI Quiz → Exam Mode → Leaderboard

---

### 🎯 Features:
- 🧠 AI Exam Generator  
- ⏱️ Timed Exams  
- 🏆 Leaderboard  
- 📊 Weak Topic Detection  
- 🎮 Game-like Learning  

---

👉 Start your learning journey below 👇
""")

# ==========================
# SIDEBAR
# ==========================
menu = st.sidebar.selectbox(
    "Choose Option",
    ["🏠 Home", "🤖 Generate Exam", "📝 Take Exam", "📊 Result"]
)

# ==========================
# HOME
# ==========================
if menu == "🏠 Home":

    st.markdown("""
    # 🧠 NeuroLearn AI

    ### 🚀 Learn Smarter. Not Harder.

    Turn your notes into:
    - 🧪 AI Exams  
    - 📊 Progress Tracking  
    - 🏆 Leaderboards  

    ---
    """)

    # PRODUCT CARDS
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("🧠 AI Quiz Generator")

    with col2:
        st.success("⏱️ Timed Exams")

    with col3:
        st.warning("🏆 Leaderboard System")

# ==========================
# UPLOAD NOTES
# ==========================
elif menu == "📄 Upload Notes":

    st.title("📄 Upload Study Notes")

    file = st.file_uploader("Upload PDF", type=["pdf"])
    text = ""

    if file:
        pdf = PdfReader(file)
        for p in pdf.pages:
            text += p.extract_text() or ""

        st.text_area("Preview", text[:2000])

        topic = st.text_input("Topic")

        if st.button("Save"):
            db = pd.read_csv(notes_file)
            db.loc[len(db)] = [topic, text]
            db.to_csv(notes_file, index=False)
            st.success("Saved!")

# ==========================
# GENERATE EXAM
# ==========================
elif menu == "🤖 Generate Exam":

    st.title("AI Exam Generator")

    db = pd.read_csv(notes_file)

    topic = st.selectbox("Topic", db["Topic"].unique())
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

    if st.button("Generate Exam"):

        notes = db[db["Topic"] == topic]["Notes"].values[0]

        st.session_state.questions = generate_mcqs(notes, difficulty)
        st.session_state.index = 0
        st.session_state.answers = {}
        st.session_state.score = 0
        st.session_state.exam_active = True

        st.success("Exam Ready!")
        st.rerun()   
# ==========================
# EXAM MODE
# ==========================
elif menu == "🧠 Exam Mode":

    st.title("🧠 Live Exam Mode")

    # ✅ SAFETY CHECK (VERY IMPORTANT)
    if "questions" not in st.session_state or len(st.session_state.questions) == 0:
        st.warning("⚠️ Generate exam first")
        st.stop()

    q = st.session_state.questions

    # ✅ INIT START TIME SAFETY
    if "start_time" not in st.session_state:
        st.warning("⚠️ Please generate exam first")
        st.stop()

    # =========================
    # TIMER
    # =========================
    elapsed = time.time() - st.session_state.start_time
    remaining = st.session_state.time_limit - elapsed

    if remaining <= 0:
        st.error("⏰ Time Up! Auto Submitting...")
        st.session_state.exam_active = False
        st.stop()

    st.progress(max(0, remaining / st.session_state.time_limit))

    # =========================
    # QUESTION DISPLAY
    # =========================
    i = st.session_state.index
    question = q[i]

    st.subheader(f"Q{i+1}. {question['question']}")

    # IMPORTANT: unique key avoids radio reset bug
    choice = st.radio("Choose:", question["options"], key=f"q_{i}")

    # =========================
    # BUTTONS
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Prev") and i > 0:
            st.session_state.answers[i] = choice
            st.session_state.index -= 1
            st.rerun()

    with col2:
        if st.button("Next ➡"):

            st.session_state.answers[i] = choice

            if i < len(q) - 1:
                st.session_state.index += 1
            else:
                st.session_state.exam_active = False
                st.success("✅ Exam Finished!")

            st.rerun()

# ==========================
# RESULT + LEADERBOARD + WEAK TOPIC
# ==========================
if st.session_state.get("exam_active") == False and st.session_state.questions:

    st.title("🎯 Result Analysis")

    q = st.session_state.questions
    ans = st.session_state.answers

    score = 0
    wrong_topics = []

    for i, item in enumerate(q):

        correct = item["options"][["A","B","C","D"].index(item["answer"])]

        if ans.get(i) == correct:
            score += 1
        else:
            wrong_topics.append(item["question"])

    st.success(f"Score: {score}/{len(q)}")

    # ================= LEADERBOARD =================
    name = st.text_input("Enter Name for Leaderboard")

    if st.button("Save Score") and name:

        lb = pd.read_csv(leaderboard_file)

        lb.loc[len(lb)] = [
            name,
            score,
            "Medium",
            "AI Exam",
            datetime.now().strftime("%Y-%m-%d")
        ]

        lb.to_csv(leaderboard_file, index=False)

        st.success("Saved to Leaderboard!")

    # ================= WEAK DETECTION =================
    st.subheader("📉 Weak Areas")

    for w in wrong_topics:
        st.warning(w)

# ==========================
# LEADERBOARD
# ==========================
elif menu == "🏆 Leaderboard":

    st.title("🏆 Top Students")

    lb = pd.read_csv(leaderboard_file)

    st.dataframe(lb.sort_values(by="Score", ascending=False))
