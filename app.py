import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

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

# ==========================
# SIDEBAR
# ==========================

menu = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📚 Add Topic",
        "📝 Take Quiz",
        "📊 Dashboard",
        "⚠ Topics At Risk",
        "🔔 Revision Alerts"
    ]
)

# ==========================
# HOME PAGE
# ==========================

if menu == "🏠 Home":

    st.title("🧠 AI Memory Assistant")

    st.markdown("""
    ### Your External Brain

    This system helps students:

    - Track studied topics
    - Take quizzes
    - Monitor memory strength
    - Identify weak topics
    - Schedule revisions
    - Improve retention
    """)

# ==========================
# ADD TOPIC PAGE
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

            memory_db.to_csv(
                memory_file,
                index=False
            )

            st.success("Topic Added Successfully!")

        else:

            st.warning(
                "Please enter topic and subject."
            )

    st.subheader("Stored Topics")

    st.dataframe(
        pd.read_csv(memory_file),
        use_container_width=True
    )

# ==========================
# TAKE QUIZ PAGE
# ==========================

elif menu == "📝 Take Quiz":

    st.title("📝 Take Quiz")

    if not os.path.exists(quiz_file):

        st.error("quiz_bank.csv not found!")

    else:

        quiz_db = pd.read_csv(quiz_file)

        topics = quiz_db["Topic"].unique()

        selected_topic = st.selectbox(
            "Select Topic",
            topics
        )

        questions = quiz_db[
            quiz_db["Topic"] == selected_topic
        ]

        answers = []

        st.subheader(
            f"Quiz: {selected_topic}"
        )

        for index, row in questions.iterrows():

            user_answer = st.text_input(
                row["Question"],
                key=index
            )

            answers.append(
                (
                    user_answer,
                    row["Answer"]
                )
            )

        if st.button("Submit Quiz"):

            correct = 0
            wrong = 0

            for user_answer, actual_answer in answers:

                if (
                    user_answer.strip().lower()
                    ==
                    str(actual_answer).strip().lower()
                ):

                    correct += 1

                else:

                    wrong += 1

            total = correct + wrong

            if total > 0:

                score = (correct / total) * 100

            else:

                score = 0

            st.success(
                f"Correct: {correct} | Wrong: {wrong}"
            )

            st.metric(
                "Memory Score",
                round(score, 2)
            )

            memory_db = pd.read_csv(memory_file)

            row_index = memory_db[
                memory_db["Topic"]
                == selected_topic
            ].index

            if len(row_index) > 0:

                idx = row_index[0]

                memory_db.loc[
                    idx,
                    "Memory_Score"
                ] = score

                memory_db.loc[
                    idx,
                    "Correct_Answers"
                ] = correct

                memory_db.loc[
                    idx,
                    "Wrong_Answers"
                ] = wrong

                memory_db.to_csv(
                    memory_file,
                    index=False
                )

                st.success(
                    "Memory Updated!"
                )

# ==========================
# DASHBOARD
# ==========================

elif menu == "📊 Dashboard":

    st.title("📊 Memory Dashboard")

    memory_db = pd.read_csv(memory_file)

    if len(memory_db) == 0:

        st.warning("No topics available.")

    else:

        st.dataframe(
            memory_db,
            use_container_width=True
        )

        fig, ax = plt.subplots()

        ax.bar(
            memory_db["Topic"],
            memory_db["Memory_Score"]
        )

        ax.set_ylabel(
            "Memory Score"
        )

        ax.set_ylim(0, 100)

        plt.xticks(rotation=20)

        st.pyplot(fig)

# ==========================
# TOPICS AT RISK
# ==========================

elif menu == "⚠ Topics At Risk":

    st.title("⚠ Topics At Risk")

    memory_db = pd.read_csv(memory_file)

    risky = memory_db[
        memory_db["Memory_Score"] < 70
    ]

    if len(risky) == 0:

        st.success(
            "🎉 No Topics At Risk"
        )

    else:

        st.dataframe(
            risky,
            use_container_width=True
        )

# ==========================
# REVISION ALERTS
# ==========================

elif menu == "🔔 Revision Alerts":

    st.title("🔔 Revision Alerts")

    memory_db = pd.read_csv(memory_file)

    st.dataframe(
        memory_db[
            [
                "Topic",
                "Next_Revision_Date",
                "Memory_Score"
            ]
        ],
        use_container_width=True
    )


