from PyPDF2 import PdfReader
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import numpy as np

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="AI Memory Assistant",
    page_icon="🧠",
    layout="wide"
)

# ==========================
# FILES
# ==========================
memory_file = "student_memory.csv"
quiz_file = "quiz_bank.csv"
notes_file = "notes_database.csv"

# ==========================
# SESSION STATE (NEW - KPI SUPPORT)
# ==========================
if "quiz_scores" not in st.session_state:
    st.session_state.quiz_scores = []

# ==========================
# CREATE MEMORY DATABASE
# ==========================
if not os.path.exists(memory_file):

    memory_db = pd.DataFrame(columns=[
        "Topic",
        "Subject",
        "Date_Studied",
        "Memory_Score",
        "Correct_Answers",
        "Wrong_Answers",
        "Average_Response_Time",
        "Next_Revision_Date"
    ])

    memory_db.to_csv(memory_file, index=False)

if not os.path.exists(notes_file):

    notes_db = pd.DataFrame(
        columns=["Topic", "Notes"]
    )

    notes_db.to_csv(
        notes_file,
        index=False
    )
# ==========================
# SIDEBAR
# ==========================
menu = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📚 Add Topic",
        "📄 Upload Notes",
        "📝 Take Quiz",
        "📊 Dashboard",
        "⚠ Topics At Risk",
        "🔔 Revision Alerts"
    ]
)

# ==========================
# 🏠 HOME (KPI DASHBOARD ADDED HERE)
# ==========================
if menu == "🏠 Home":

    st.title("🧠 AI Memory Assistant")

    st.markdown("### Your Personal Learning Intelligence System")

    st.divider()

    col1, col2, col3 = st.columns(3)

    total_topics = len(pd.read_csv(memory_file))

    total_quizzes = len(st.session_state.quiz_scores)

    avg_score = (
        np.mean(st.session_state.quiz_scores)
        if st.session_state.quiz_scores else 0
    )

    with col1:
        st.metric("📚 Topics Stored", total_topics)

    with col2:
        st.metric("📝 Quizzes Taken", total_quizzes)

    with col3:
        st.metric("🧠 Avg Score", f"{avg_score:.2f}")

    st.divider()

    st.info("💡 Tip: Take quizzes regularly to improve your memory score!")

# ==========================
# 📚 ADD TOPIC
# ==========================
elif menu == "📚 Add Topic":

    st.title("📚 Add New Topic")

    topic = st.text_input("Topic Name")
    subject = st.text_input("Subject Name")

    if st.button("Save Topic"):

        if topic and subject:

            memory_db = pd.read_csv(memory_file)

            new_row = {
                "Topic": topic,
                "Subject": subject,
                "Date_Studied": datetime.now().date(),
                "Memory_Score": 100,
                "Correct_Answers": 0,
                "Wrong_Answers": 0,
                "Average_Response_Time": 0,
                "Next_Revision_Date": datetime.now().date()
            }

            memory_db.loc[len(memory_db)] = new_row
            memory_db.to_csv(memory_file, index=False)

            st.success("Topic Added Successfully!")

        else:
            st.warning("Please enter topic and subject.")

    st.subheader("Stored Topics")
    st.dataframe(pd.read_csv(memory_file), use_container_width=True)


# ==========================
# 📄 UPLOAD NOTES
# ==========================

elif menu == "📄 Upload Notes":

    st.title("📄 Upload Notes")

    uploaded_file = st.file_uploader(
        "Upload a PDF file",
        type=["pdf"]
    )

    if uploaded_file is not None:

        pdf = PdfReader(uploaded_file)

        extracted_text = ""

        for page in pdf.pages:
            extracted_text += page.extract_text() + "\n"

        st.success("PDF processed successfully!")

        st.subheader("📖 Extracted Text Preview")

        st.text_area(
            "Preview",
            extracted_text[:5000],
            height=300
        )
    topic_name = st.text_input(
    "Enter Topic Name"
)

if st.button("💾 Save Notes"):

    if topic_name.strip() == "":
        st.warning("Please enter a topic name.")

    else:

        notes_db = pd.read_csv(notes_file)

        new_note = {
            "Topic": topic_name,
            "Notes": extracted_text
        }

        notes_db.loc[len(notes_db)] = new_note

        notes_db.to_csv(
            notes_file,
            index=False
        )

        st.success("Notes Saved Successfully!")    
# ==========================
# 📝 TAKE QUIZ (UPDATED - KPI TRACKING)
# ==========================
elif menu == "📝 Take Quiz":

    st.title("📝 Take Quiz")

    if not os.path.exists(quiz_file):
        st.error("quiz_bank.csv not found!")

    else:

        quiz_db = pd.read_csv(quiz_file)
        topics = quiz_db["Topic"].unique()

        selected_topic = st.selectbox("Select Topic", topics)

        questions = quiz_db[quiz_db["Topic"] == selected_topic]

        answers = []

        st.subheader(f"Quiz: {selected_topic}")

        for index, row in questions.iterrows():

            user_answer = st.text_input(row["Question"], key=str(index))
            answers.append((user_answer, row["Answer"]))

        if st.button("Submit Quiz"):

            correct = 0
            wrong = 0

            for user_answer, actual_answer in answers:

                if user_answer.strip().lower() == str(actual_answer).strip().lower():
                    correct += 1
                else:
                    wrong += 1

            total = correct + wrong

            score = (correct / total) * 100 if total > 0 else 0

            st.success(f"Correct: {correct} | Wrong: {wrong}")
            st.metric("Memory Score", round(score, 2))

            # ==========================
            # SAVE KPI DATA (NEW)
            # ==========================
            st.session_state.quiz_scores.append(score)

            # ==========================
            # UPDATE MEMORY FILE
            # ==========================
            memory_db = pd.read_csv(memory_file)

            row_index = memory_db[memory_db["Topic"] == selected_topic].index

            if len(row_index) > 0:

                idx = row_index[0]

                memory_db.loc[idx, "Memory_Score"] = score
                memory_db.loc[idx, "Correct_Answers"] = correct
                memory_db.loc[idx, "Wrong_Answers"] = wrong

                memory_db.to_csv(memory_file, index=False)

                st.success("Memory Updated!")

# ==========================
# 📊 DASHBOARD (UPGRADED GRAPH)
# ==========================
elif menu == "📊 Dashboard":

    st.title("📊 AI Learning Analytics Dashboard")

    memory_db = pd.read_csv(memory_file)

    if len(memory_db) == 0:
        st.warning("No topics available.")

    else:

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Topic Performance")

            fig1, ax1 = plt.subplots()
            ax1.bar(memory_db["Topic"], memory_db["Memory_Score"])
            ax1.set_ylim(0, 100)
            plt.xticks(rotation=25)

            st.pyplot(fig1)

        with col2:
            st.subheader("📈 Learning Trend")

            if len(st.session_state.quiz_scores) > 0:

                fig2, ax2 = plt.subplots()

                ax2.plot(
                    range(1, len(st.session_state.quiz_scores) + 1),
                    st.session_state.quiz_scores,
                    marker="o"
                )

                ax2.set_ylim(0, 100)

                st.pyplot(fig2)

            else:
                st.info("No quiz data yet")
        # ==========================
        # 📊 BAR CHART: Topic vs Memory Score
        # ==========================
        st.subheader("📊 Topic Performance")

        fig1, ax1 = plt.subplots()

        ax1.bar(
            memory_db["Topic"],
            memory_db["Memory_Score"]
        )

        ax1.set_ylabel("Memory Score")
        ax1.set_ylim(0, 100)
        plt.xticks(rotation=25)

        st.pyplot(fig1)

        # ==========================
        # 📉 LINE CHART: Quiz Score Trend
        # ==========================
        st.subheader("📉 Learning Progress Trend")

        if len(st.session_state.quiz_scores) > 0:

            fig2, ax2 = plt.subplots()

            ax2.plot(
                range(1, len(st.session_state.quiz_scores) + 1),
                st.session_state.quiz_scores,
                marker="o"
            )

            ax2.set_xlabel("Quiz Attempt")
            ax2.set_ylabel("Score")
            ax2.set_ylim(0, 100)

            st.pyplot(fig2)

        else:
            st.info("Take quizzes to see progress trend 📊")
# ==========================
# ⚠ TOPICS AT RISK
# ==========================
elif menu == "⚠ Topics At Risk":

    st.title("⚠ Topics At Risk")

    memory_db = pd.read_csv(memory_file)

    risky = memory_db[memory_db["Memory_Score"] < 70]

    if len(risky) == 0:
        st.success("🎉 No Topics At Risk")

    else:
        st.dataframe(risky, use_container_width=True)

# ==========================
# 🔔 REVISION ALERTS
# ==========================
elif menu == "🔔 Revision Alerts":

    st.title("🔔 Revision Alerts")

    memory_db = pd.read_csv(memory_file)

    st.dataframe(
        memory_db[["Topic", "Next_Revision_Date", "Memory_Score"]],
        use_container_width=True
    )
