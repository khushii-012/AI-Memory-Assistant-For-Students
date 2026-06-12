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

/* GLOBAL BACKGROUND */
.main {
    background: linear-gradient(135deg, #0f1117, #1a1d24);
}

/* TITLE */
h1 {
    text-align: center;
    color: #00ffcc;
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 10px;
}

/* SUBTITLE */
.subtitle {
    text-align: center;
    color: #aaa;
    font-size: 18px;
    margin-bottom: 40px;
}

/* FEATURE CARD */
.feature-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(0,255,204,0.2);
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    transition: 0.3s;
    cursor: pointer;
    box-shadow: 0 0 15px rgba(0,255,204,0.05);
}

.feature-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 0 25px rgba(0,255,204,0.3);
    border: 1px solid rgba(0,255,204,0.6);
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg, #00ffcc, #00b3ff);
    color: black;
    border-radius: 12px;
    height: 3em;
    font-weight: bold;
    width: 100%;
    border: none;
}

/* BADGE STYLE */
.badge {
    background: #00ffcc;
    color: black;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
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

    st.title("🧠 NeuroLearn AI")
    st.markdown('<p class="subtitle">Turn your notes into smart exams with AI-powered learning</p>', unsafe_allow_html=True)

    st.markdown("---")

    # TOP STATS SECTION
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 Notes Engine</h3>
            <p>Upload PDF & convert into AI-ready knowledge</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Notes"):
            st.session_state.page = "upload"

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🤖 AI Exam Generator</h3>
            <p>Auto-generate MCQs using LLM intelligence</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Generate Exam"):
            st.session_state.page = "generate"

    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🧠 Live Exam Mode</h3>
            <p>Timed exam with smart navigation system</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Start Exam"):
            st.session_state.page = "exam"

    st.markdown("---")

    # SECOND ROW
    col4, col5 = st.columns(2)

    with col4:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Analytics Dashboard</h3>
            <p>View performance, score & weak areas</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("View Results"):
            st.session_state.page = "result"

    with col5:
        st.markdown("""
        <div class="feature-card">
            <h3>🏆 Leaderboard</h3>
            <p>Compete with top learners & track ranking</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("View Leaderboard"):
            st.session_state.page = "leaderboard"

    st.markdown("---")

    # BOTTOM INFO PANEL
    st.markdown("""
    <div style='text-align:center; padding:20px; color:#888;'>
        ⚡ Powered by Groq AI • Built for Smart Learning • NeuroLearn v2.0
    </div>
    """, unsafe_allow_html=True)

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
