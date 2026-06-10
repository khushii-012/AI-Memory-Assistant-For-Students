import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(
    page_title="AI Memory Assistant",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 AI Memory Assistant for Students")

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

st.header("➕ Add New Topic")

topic = st.text_input("Topic Name")

subject = st.text_input("Subject")

if st.button("Save Topic"):

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

st.header("📚 Stored Topics")

memory_db = pd.read_csv(memory_file)

st.dataframe(memory_db)
