from PyPDF2 import PdfReader
import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from groq import Groq

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(page_title="NeuroLearn AI", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    body { background-color: #0f1117; color: white; }
    .main { background-color: #0f1117; }

    h1, h2, h3 { color: #00ffcc; text-align: center; }

    /* FEATURE CARDS */
    .card {
        background-color: #1a1d24;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        cursor: pointer;
        transition: 0.3s;
        box-shadow: 0px 0px 10px rgba(0,255,204,0.2);
    }

    .card:hover {
        transform: scale(1.05);
        box-shadow: 0px 0px 20px rgba(0,255,204,0.5);
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
    }

    .btn {
        background-color: #00ffcc;
        padding: 10px;
        border-radius: 10px;
        color: black;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# SESSION STATE
# ==========================
defaults = {
    "page": "home",
    "questions": [],
    "index": 0,
    "answers": {},
    "start_time": None,
    "time_limit": 120
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==========================
# FILES
# ==========================
notes_file = "notes.csv"
leaderboard_file = "leaderboard.csv"

if not os.path.exists(notes_file):
    pd.DataFrame(columns=["Topic", "Notes"]).to_csv(notes_file, index=False)

if not os.path.exists(leaderboard_file):
    pd.DataFrame(columns=["Name", "Score", "Badge", "Date"]).to_csv(leaderboard_file, index=False)

# ==========================
# AI ENGINE
# ==========================
def generate_mcqs(notes, difficulty):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
Generate 5 MCQs.

Difficulty: {difficulty}

Return JSON:
{{
 "questions": [
  {{
   "question": "...",
   "options": ["A","B","C","D"],
   "answer": "A",
   "explanation": "short explanation"
  }}
 ]
}}

Notes:
{notes[:2500]}
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
# HOME PAGE (MODERN DASHBOARD)
# ==========================
def home():

    st.title("🧠 NeuroLearn AI Dashboard")

    st.markdown("### 🚀 Choose what you want to do")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Upload Notes"):
            st.session_state.page = "upload"

    with col2:
        if st.button("🤖 Generate Exam"):
            st.session_state.page = "generate"

    with col3:
        if st.button("🧠 Take Exam"):
            st.session_state.page = "exam"

    col4, col5, col6 = st.columns(3)

    with col4:
        if st.button("📊 Results"):
            st.session_state.page = "result"

    with col5:
        if st.button("🏆 Leaderboard"):
            st.session_state.page = "leaderboard"

    with col6:
        st.info("🔥 AI Powered Learning System")

# ==========================
# UPLOAD
# ==========================
def upload():

    st.title("📄 Upload Notes")

    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        text = ""
        pdf = PdfReader(file)

        for p in pdf.pages:
            text += p.extract_text() or ""

        topic = st.text_input("Topic")

        if st.button("Save") and topic:
            db = pd.read_csv(notes_file)
            db.loc[len(db)] = [topic, text]
            db.to_csv(notes_file, index=False)
            st.success("Saved!")

# ==========================
# GENERATE EXAM
# ==========================
def generate():

    st.title("🤖 Generate Exam")

    db = pd.read_csv(notes_file)

    if len(db) == 0:
        st.warning("Upload notes first")
        return

    topic = st.selectbox("Topic", db["Topic"].unique())
    difficulty = st.selectbox("Difficulty", ["Easy","Medium","Hard"])

    if st.button("Generate"):

        notes = db[db["Topic"] == topic]["Notes"].values[0]

        st.session_state.questions = generate_mcqs(notes, difficulty)
        st.session_state.index = 0
        st.session_state.answers = {}
        st.session_state.start_time = time.time()

        st.success("Exam Ready!")

# ==========================
# EXAM MODE
# ==========================
def exam():

    st.title("🧠 Exam Mode")

    q = st.session_state.questions

    if not q:
        st.warning("Generate exam first")
        return

    i = st.session_state.index
    question = q[i]

    st.write(f"Q{i+1}. {question['question']}")

    choice = st.radio("Answer:", question["options"], key=i)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Prev") and i > 0:
            st.session_state.index -= 1
            st.rerun()

    with col2:
        if st.button("Next ➡"):

            st.session_state.answers[i] = choice

            if i < len(q)-1:
                st.session_state.index += 1

            st.rerun()

# ==========================
# RESULT
# ==========================
def result():

    st.title("📊 Results")

    q = st.session_state.questions
    ans = st.session_state.answers

    if not q:
        st.warning("No exam found")
        return

    score = 0

    for i, item in enumerate(q):
        if ans.get(i) == item["answer"]:
            score += 1

    st.success(f"Score: {score}/{len(q)}")

    if score >= 4:
        st.info("🏆 Badge: Genius")
    elif score >= 3:
        st.info("🥈 Badge: Smart")
    else:
        st.info("📘 Badge: Learner")

# ==========================
# LEADERBOARD
# ==========================
def leaderboard():

    st.title("🏆 Leaderboard")

    lb = pd.read_csv(leaderboard_file)
    st.dataframe(lb)

# ==========================
# ROUTER
# ==========================
if st.session_state.page == "home":
    home()

elif st.session_state.page == "upload":
    upload()

elif st.session_state.page == "generate":
    generate()

elif st.session_state.page == "exam":
    exam()

elif st.session_state.page == "result":
    result()

elif st.session_state.page == "leaderboard":
    leaderboard()
