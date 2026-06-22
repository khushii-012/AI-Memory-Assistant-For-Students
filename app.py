from PyPDF2 import PdfReader
import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from groq import Groq

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="NeuroLearn AI",
    page_icon="🧠",
    layout="wide"
)

# =====================================
# CUSTOM CSS
# =====================================
st.markdown("""
<style>

.main {
    background: linear-gradient(135deg, #0f1117, #1a1d24);
}

h1,h2,h3 {
    color: #00ffcc;
}

.subtitle {
    text-align:center;
    color:#aaa;
    font-size:18px;
}

.feature-card {
    background: rgba(255,255,255,0.05);
    border:1px solid rgba(0,255,204,0.2);
    padding:25px;
    border-radius:18px;
    text-align:center;
    box-shadow:0 0 15px rgba(0,255,204,0.05);
}

.stButton > button {
    background: linear-gradient(90deg,#00ffcc,#00b3ff);
    color:black;
    border:none;
    border-radius:12px;
    font-weight:bold;
    height:3em;
    width:100%;
}

.badge {
    background:#00ffcc;
    color:black;
    padding:6px 14px;
    border-radius:20px;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# SESSION STATE
# =====================================
defaults = {
    "page": "home",
    "questions": [],
    "answers": {},
    "current_question": 0,
    "score": 0,
    "exam_submitted": False,
    "start_time": None,
    "time_limit": 300,
    "current_topic": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =====================================
# FILES
# =====================================
NOTES_FILE = "notes.csv"
LEADERBOARD_FILE = "leaderboard.csv"

if not os.path.exists(NOTES_FILE):
    pd.DataFrame(
        columns=["Topic", "Notes"]
    ).to_csv(NOTES_FILE, index=False)

if not os.path.exists(LEADERBOARD_FILE):
    pd.DataFrame(
        columns=[
            "Name",
            "Score",
            "Badge",
            "Topic",
            "Date"
        ]
    ).to_csv(LEADERBOARD_FILE, index=False)

# =====================================
# NAVIGATION
# =====================================
def go_home():
    st.session_state.page = "home"
    st.rerun()

def top_bar():

    col1, col2, col3 = st.columns([1,5,1])

    with col1:
        if st.button("🏠 Home"):
            go_home()

    with col3:
        st.markdown("### 🧠")

# =====================================
# LOAD DATA
# =====================================
def load_notes():
    return pd.read_csv(NOTES_FILE)

def load_leaderboard():
    return pd.read_csv(LEADERBOARD_FILE)

# =====================================
# SAVE NOTE
# =====================================
def save_note(topic, text):

    db = load_notes()

    db.loc[len(db)] = [
        topic,
        text
    ]

    db.to_csv(
        NOTES_FILE,
        index=False
    )

# =====================================
# BADGE LOGIC
# =====================================
def get_badge(score, total):

    if total == 0:
        return "Learner"

    percent = (score / total) * 100

    if percent >= 90:
        return "🏆 Genius"

    elif percent >= 70:
        return "🥈 Smart"

    elif percent >= 50:
        return "📘 Learner"

    return "🌱 Beginner"

# =====================================
# AI EXAM GENERATOR
# =====================================
def generate_mcqs(notes, difficulty):

    client = Groq(
        api_key=st.secrets["GROQ_API_KEY"]
    )

    prompt = f"""
You are an exam creator.

Generate exactly 5 MCQs.

Difficulty: {difficulty}

Return ONLY valid JSON.

Format:

{
  "question":"...",
  "options":[
      "Option A",
      "Option B",
      "Option C",
      "Option D"
  ],
  "answer":"Option A",
  "explanation":"..."
}

Notes:

{notes[:3000]}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role":"user",
                    "content":prompt
                }
            ],
            temperature=0.2
        )

        raw = response.choices[0].message.content

        cleaned = (
            raw
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        data = json.loads(cleaned)

        return data.get("questions", [])

    except Exception as e:

        st.error(f"AI Error: {e}")

        return []

# =====================================
# EXAM RESET
# =====================================
def reset_exam():

    st.session_state.questions = []
    st.session_state.answers = {}
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.exam_submitted = False
    st.session_state.start_time = None


# =====================================
# HOME PAGE
# =====================================
def home():

    st.title("🧠 NeuroLearn AI")

    st.markdown(
        '<p class="subtitle">Turn your notes into smart AI-powered exams</p>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    # =====================
    # STATS
    # =====================
    notes_count = len(load_notes())

    try:
        lb = load_leaderboard()

        if len(lb) > 0:
            avg_score = round(lb["Score"].mean(), 2)
        else:
            avg_score = 0

    except:
        avg_score = 0

    s1, s2, s3 = st.columns(3)

    with s1:
        st.metric("📄 Notes Uploaded", notes_count)

    with s2:
        st.metric("📝 Exams Taken", len(load_leaderboard()))

    with s3:
        st.metric("📊 Average Score", avg_score)

    st.markdown("---")

    # =====================
    # CARDS
    # =====================
    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("""
        <div class="feature-card">
        <h3>📄 Upload Notes</h3>
        <p>Upload PDF study material</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Notes"):
            st.session_state.page = "upload"
            st.rerun()

    with col2:

        st.markdown("""
        <div class="feature-card">
        <h3>🤖 Generate Exam</h3>
        <p>Create MCQs instantly using AI</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Generate Exam"):
            st.session_state.page = "generate"
            st.rerun()

    with col3:

        st.markdown("""
        <div class="feature-card">
        <h3>🏆 Leaderboard</h3>
        <p>View top learners</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Leaderboard"):
            st.session_state.page = "leaderboard"
            st.rerun()

    st.markdown("---")

    # =====================
    # CONTINUE EXAM
    # =====================
    if len(st.session_state.questions) > 0:

        st.success("✅ Exam Ready")

        if st.button("🚀 Continue Exam"):
            st.session_state.page = "exam"
            st.rerun()

    st.markdown("---")

    st.markdown(
        """
        <center>
        ⚡ Powered by Groq AI <br>
        NeuroLearn AI v2.0
        </center>
        """,
        unsafe_allow_html=True
    )


# =====================================
# UPLOAD PAGE
# =====================================
def upload():

    top_bar()

    st.title("📄 Upload Notes")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if file:

        text = ""

        pdf = PdfReader(file)

        for page in pdf.pages:
            text += page.extract_text() or ""

        st.text_area(
            "Preview",
            text[:2000],
            height=250
        )

        topic = st.text_input(
            "Topic Name"
        )

        if st.button("💾 Save Notes"):

            if topic.strip() == "":
                st.warning("Enter topic name")
                return

            save_note(topic, text)

            st.success("Notes Saved Successfully")

            st.dataframe(load_notes())


# =====================================
# GENERATE EXAM
# =====================================
def generate():

    top_bar()

    st.title("🤖 Generate Exam")

    db = load_notes()

    if len(db) == 0:

        st.warning(
            "Upload notes first"
        )

        return

    topic = st.selectbox(
        "Select Topic",
        db["Topic"].unique()
    )

    difficulty = st.selectbox(
        "Difficulty",
        [
            "Easy",
            "Medium",
            "Hard"
        ]
    )

    if st.button("⚡ Generate AI Exam"):

        with st.spinner(
            "Generating Questions..."
        ):

            notes = db[
                db["Topic"] == topic
            ]["Notes"].values[0]

            questions = generate_mcqs(
                notes,
                difficulty
            )

            if len(questions) == 0:

                st.error(
                    "AI failed to generate questions"
                )

                return

            st.session_state.questions = questions
            st.session_state.answers = {}
            st.session_state.current_question = 0
            st.session_state.exam_submitted = False
            st.session_state.current_topic = topic
            st.session_state.start_time = time.time()

            st.success(
                "Exam Generated Successfully"
            )

            # AUTO OPEN EXAM
            st.session_state.page = "exam"
            st.rerun()


# =====================================
# EXAM PAGE
# =====================================
def exam():

    top_bar()

    st.title("🧠 Live Exam")

    questions = st.session_state.questions

    if len(questions) == 0:

        st.warning(
            "Generate exam first"
        )

        return

    # =====================
    # TIMER
    # =====================
    elapsed = (
        time.time()
        - st.session_state.start_time
    )

    remaining = max(
        0,
        st.session_state.time_limit
        - elapsed
    )

    st.progress(
        remaining
        / st.session_state.time_limit
    )

    mins = int(remaining // 60)
    secs = int(remaining % 60)

    st.info(
        f"⏳ Time Left: {mins}:{secs:02d}"
    )

    if remaining <= 0:

        st.session_state.page = "result"
        st.rerun()

    # =====================
    # QUESTION PALETTE
    # =====================
    st.subheader(
        "Question Palette"
    )

    palette_cols = st.columns(
        len(questions)
    )

    for idx in range(len(questions)):

        with palette_cols[idx]:

            if st.button(
                str(idx + 1),
                key=f"nav_{idx}"
            ):
                st.session_state.current_question = idx
                st.rerun()

    st.markdown("---")

    i = st.session_state.current_question

    q = questions[i]

    st.subheader(
        f"Question {i+1}/{len(questions)}"
    )

    st.write(q["question"])

    previous_answer = (
        st.session_state.answers.get(i)
    )

    selected = st.radio(
        "Choose Answer",
        q["options"],
        index=(
            q["options"].index(previous_answer)
            if previous_answer in q["options"]
            else None
        ),
        key=f"q_{i}"
    )

    st.session_state.answers[i] = selected

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button("⬅ Previous"):

            if i > 0:

                st.session_state.current_question -= 1
                st.rerun()

    with col2:

        if st.button("✅ Submit Exam"):

            st.session_state.page = "result"
            st.rerun()

    with col3:

        if st.button("Next ➡"):

            if i < len(questions) - 1:

                st.session_state.current_question += 1
                st.rerun()


# =====================================
# RESULT PAGE
# =====================================
def result():

    top_bar()

    st.title("📊 Exam Results")

    questions = st.session_state.questions

    if len(questions) == 0:
        st.warning("No exam found")
        return

    score = 0

    st.markdown("---")

    for i, q in enumerate(questions):

        user_answer = st.session_state.answers.get(i)

        correct_answer = q["answer"]

        if user_answer == correct_answer:
            score += 1
            st.success(
                f"Q{i+1}: Correct ✅"
            )
        else:
            st.error(
                f"Q{i+1}: Incorrect ❌"
            )

        st.write(
            f"**Question:** {q['question']}"
        )

        st.write(
            f"**Your Answer:** {user_answer}"
        )

        st.write(
            f"**Correct Answer:** {correct_answer}"
        )

        if "explanation" in q:
            st.info(
                f"💡 {q['explanation']}"
            )

        st.markdown("---")

    # =====================
    # SCORE
    # =====================
    total = len(questions)

    badge = get_badge(
        score,
        total
    )

    st.session_state.score = score

    st.success(
        f"🎯 Final Score: {score}/{total}"
    )

    st.markdown(
        f"### {badge}"
    )

    # =====================
    # PERFORMANCE
    # =====================
    percent = round(
        (score / total) * 100,
        2
    )

    st.metric(
        "Performance",
        f"{percent}%"
    )

    # =====================
    # SAVE SCORE
    # =====================
    st.markdown("---")

    name = st.text_input(
        "Enter Your Name"
    )

    if st.button("🏆 Save Score"):

        if name.strip() == "":
            st.warning(
                "Enter your name"
            )
            return

        lb = load_leaderboard()

        lb.loc[len(lb)] = [
            name,
            score,
            badge,
            st.session_state.current_topic,
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        ]

        lb.to_csv(
            LEADERBOARD_FILE,
            index=False
        )

        st.success(
            "Score Saved"
        )

    # =====================
    # ACTION BUTTONS
    # =====================
    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🏠 Back To Home"
        ):
            go_home()

    with col2:

        if st.button(
            "🔄 New Exam"
        ):

            reset_exam()

            st.session_state.page = "generate"

            st.rerun()


# =====================================
# LEADERBOARD PAGE
# =====================================
def leaderboard():

    top_bar()

    st.title("🏆 Leaderboard")

    lb = load_leaderboard()

    if len(lb) == 0:

        st.info(
            "No scores yet"
        )

        return

    lb = lb.sort_values(
        by="Score",
        ascending=False
    )

    st.dataframe(
        lb,
        use_container_width=True
    )

    st.markdown("---")

    st.subheader(
        "Top Performer"
    )

    top = lb.iloc[0]

    st.success(
        f"{top['Name']} • {top['Score']} • {top['Badge']}"
    )


# =====================================
# ROUTER
# =====================================
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
