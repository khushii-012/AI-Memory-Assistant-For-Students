from PyPDF2 import PdfReader
import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from groq import Groq

# ==========================
# PAGE CONFIG (HackerRank STYLE)
# ==========================
st.set_page_config(
    page_title="NeuroLearn AI",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
    body { background-color: #0f1117; color: white; }
    .main { background-color: #0f1117; }
    h1, h2, h3 { color: #00ffcc; text-align: center; }

    .stButton>button {
        background-color: #00ffcc;
        color: black;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }

    .card {
        padding: 20px;
        background-color: #1a1d24;
        border-radius: 12px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# SESSION STATE INIT (SAFE)
# ==========================
defaults = {
    "questions": [],
    "index": 0,
    "answers": {},
    "exam_active": False,
    "start_time": None,
    "time_limit": 120,
    "score": 0,
    "feedback": ""
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

Return ONLY JSON:
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
# SIDEBAR
# ==========================
menu = st.sidebar.selectbox(
    "Menu",
    ["🏠 Home", "📄 Upload Notes", "🤖 Generate Exam", "🧠 Exam Mode", "📊 Result", "🏆 Leaderboard"]
)

# ==========================
# HOME
# ==========================
if menu == "🏠 Home":

    st.title("🧠 NeuroLearn AI")

    st.markdown("""
    <div class='card'>
    🚀 Upload Notes → AI generates exam → You take test → Get AI feedback + rank
    </div>
    """, unsafe_allow_html=True)

# ==========================
# UPLOAD NOTES
# ==========================
elif menu == "📄 Upload Notes":

    st.title("📄 Upload Notes")

    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        text = ""
        pdf = PdfReader(file)

        for p in pdf.pages:
            text += p.extract_text() or ""

        st.text_area("Preview", text[:2000])

        topic = st.text_input("Topic")

        if st.button("Save Notes") and topic:
            db = pd.read_csv(notes_file)
            db.loc[len(db)] = [topic, text]
            db.to_csv(notes_file, index=False)
            st.success("Saved!")

# ==========================
# GENERATE EXAM
# ==========================
elif menu == "🤖 Generate Exam":

    st.title("🤖 AI Exam Generator")

    db = pd.read_csv(notes_file)

    if len(db) == 0:
        st.warning("Upload notes first")
        st.stop()

    topic = st.selectbox("Topic", db["Topic"].unique())
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

    if st.button("Generate Exam"):

        notes = db[db["Topic"] == topic]["Notes"].values[0]

        st.session_state.questions = generate_mcqs(notes, difficulty)
        st.session_state.index = 0
        st.session_state.answers = {}
        st.session_state.exam_active = True
        st.session_state.start_time = time.time()

        st.success("Exam Generated!")
        st.rerun()

# ==========================
# EXAM MODE
# ==========================
elif menu == "🧠 Exam Mode":

    st.title("🧠 Live Exam Mode")

    if len(st.session_state.questions) == 0:
        st.warning("Generate exam first")
        st.stop()

    q = st.session_state.questions
    i = st.session_state.index

    # TIMER
    elapsed = time.time() - st.session_state.start_time
    remaining = st.session_state.time_limit - elapsed

    if remaining <= 0:
        st.error("⏰ Time Up!")
        st.session_state.exam_active = False
        st.stop()

    st.progress(remaining / st.session_state.time_limit)

    question = q[i]

    st.markdown(f"### Q{i+1}. {question['question']}")

    choice = st.radio("Choose:", question["options"], key=f"q_{i}")

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
                st.success("Exam Completed!")

            st.rerun()

# ==========================
# RESULT + AI FEEDBACK + RANK
# ==========================
elif menu == "📊 Result":

    if not st.session_state.questions:
        st.warning("No exam found")
        st.stop()

    q = st.session_state.questions
    ans = st.session_state.answers

    score = 0
    wrong = []

    for i, item in enumerate(q):

        correct = item["answer"]
        selected = ans.get(i)

        if selected == correct:
            score += 1
        else:
            wrong.append(item)

    st.success(f"Score: {score}/{len(q)}")

    # ================= BADGE SYSTEM =================
    if score >= 4:
        badge = "🏆 Genius"
    elif score >= 3:
        badge = "🥈 Smart"
    else:
        badge = "📘 Learner"

    st.info(f"Your Badge: {badge}")

    # ================= AI FEEDBACK =================
    if wrong:

        st.subheader("📉 AI Feedback")

        for w in wrong:
            st.warning(f"{w['question']}")
            st.info(f"Explanation: {w.get('explanation','No explanation')}")

    # ================= SAVE LEADERBOARD =================
    name = st.text_input("Enter Name")

    if st.button("Save Result") and name:

        lb = pd.read_csv(leaderboard_file)

        lb.loc[len(lb)] = [
            name,
            score,
            badge,
            datetime.now().strftime("%Y-%m-%d")
        ]

        lb.to_csv(leaderboard_file, index=False)

        st.success("Saved!")

# ==========================
# LEADERBOARD
# ==========================
elif menu == "🏆 Leaderboard":

    st.title("🏆 Leaderboard")

    lb = pd.read_csv(leaderboard_file)

    st.dataframe(lb.sort_values(by="Score", ascending=False))
