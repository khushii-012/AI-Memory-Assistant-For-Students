import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="AI Memory Assistant",
    page_icon="🧠",
    layout="wide"
)

# ----------------------------
# DATABASE SETUP
# ----------------------------
memory_file = "student_memory.csv"

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

# ----------------------------
# SIDEBAR
# ----------------------------
menu = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📚 Add Topic",
        "📊 Dashboard",
        "⚠ Topics At Risk",
        "🔔 Revision Alerts"
    ]
)

# ----------------------------
# HOME PAGE
# ----------------------------
if menu == "🏠 Home":

    st.title("🧠 AI Memory Assistant for Students")

    st.markdown("""
    ### Your External Brain

    This system helps students:

    - Track studied topics
    - Monitor memory strength
    - Predict forgetting
    - Schedule revision
    - Improve long-term retention

    ### How it Works

    1. Add topics you study
    2. Take quizzes
    3. System calculates memory strength
    4. Weak topics are identified
    5. Smart revision reminders are generated
    """)

# ----------------------------
# ADD TOPIC PAGE
# ----------------------------
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
            st.warning("Please enter topic and subject.")

    st.subheader("Stored Topics")

    st.dataframe(
        pd.read_csv(memory_file),
        use_container_width=True
    )

# ----------------------------
# DASHBOARD
# ----------------------------
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

        st.subheader("Memory Strength Analysis")

        fig, ax = plt.subplots(figsize=(8,4))

        ax.bar(
            memory_db["Topic"],
            memory_db["Memory_Score"]
        )

        ax.set_ylabel("Memory Score")
        ax.set_ylim(0,100)

        plt.xticks(rotation=20)

        st.pyplot(fig)

# ----------------------------
# TOPICS AT RISK
# ----------------------------
elif menu == "⚠ Topics At Risk":

    st.title("⚠ Topics At Risk")

    memory_db = pd.read_csv(memory_file)

    risky = memory_db[
        memory_db["Memory_Score"] < 70
    ]

    if len(risky) == 0:

        st.success(
            "🎉 No topics are currently at risk!"
        )

    else:

        st.dataframe(
            risky,
            use_container_width=True
        )

# ----------------------------
# REVISION ALERTS
# ----------------------------
elif menu == "🔔 Revision Alerts":

    st.title("🔔 Smart Revision Alerts")

    memory_db = pd.read_csv(memory_file)

    if len(memory_db) == 0:

        st.warning("No topics available.")

    else:

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
