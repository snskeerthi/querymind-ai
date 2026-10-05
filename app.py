import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from google import genai
from google.genai import types

# ------------------------------------------------------------------------------
# 1. Streamlit Page Config & Title
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="QueryMind AI - Text-to-SQL",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔍 QueryMind AI — Text-to-SQL Assistant")
st.caption("Ask questions in plain English, get executed SQL queries, data tables, and instant charts.")

# ------------------------------------------------------------------------------
# 2. Database Setup (Sample SQLite DB Creation)
# ------------------------------------------------------------------------------
DB_FILE = "student_data.db"

def init_sample_database():
    """Initializes a sample SQLite database for demonstration."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create Table 1: STUDENTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS STUDENTS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME VARCHAR(50),
            CLASS VARCHAR(20),
            SECTION VARCHAR(5),
            MARKS INT,
            GRADE VARCHAR(2)
        )
    """)
    
    # Insert mock records if empty
    cursor.execute("SELECT COUNT(*) FROM STUDENTS")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('Aarav Sharma', 'Data Science', 'A', 92, 'A+'),
            ('Diya Patel', 'Data Science', 'B', 85, 'A'),
            ('Rohan Verma', 'Web Dev', 'A', 78, 'B+'),
            ('Ananya Rao', 'Web Dev', 'B', 64, 'C'),
            ('Kabir Singh', 'Data Science', 'A', 95, 'A+'),
            ('Meera Nair', 'Cybersecurity', 'A', 88, 'A'),
            ('Siddharth Gupta', 'Cybersecurity', 'B', 72, 'B'),
            ('Priya Joshi', 'Data Science', 'A', 90, 'A+'),
            ('Vikram Reddi', 'Web Dev', 'A', 81, 'A'),
            ('Sneha Kulkarni', 'Cybersecurity', 'A', 94, 'A+')
        ]
        cursor.executemany(
            "INSERT INTO STUDENTS (NAME, CLASS, SECTION, MARKS, GRADE) VALUES (?, ?, ?, ?, ?)",
            sample_data
        )
        conn.commit()
    conn.close()

init_sample_database()

# Function to get Database Schema info for Gemini
def get_db_schema():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_info = ""
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        col_names = [f"{col[1]} ({col[2]})" for col in columns]
        schema_info += f"Table '{table_name}': {', '.join(col_names)}\n"
    conn.close()
    return schema_info

# Function to execute raw SQL and return a Pandas DataFrame
def execute_sql_query(sql_query):
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df, None
    except Exception as e:
        conn.close()
        return None, str(e)

# ------------------------------------------------------------------------------
# 3. Gemini API Client Setup
# ------------------------------------------------------------------------------
@st.cache_resource
def get_client():
    return genai.Client()

try:
    client = get_client()
except Exception as e:
    st.error(f"Failed to connect to Gemini API: {e}")
    st.info("Make sure `GEMINI_API_KEY` is set in your environment variables.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. Sidebar Controls & Schema Explorer
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧠 Engine Settings")
    selected_model = st.selectbox(
        "Gemini Model",
        ["gemini-3.8-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("## 🗄️ Database Schema")
    schema_text = get_db_schema()
    st.code(schema_text, language="sql")
    
    if st.button("👁️ View Full Database Table"):
        df_all, _ = execute_sql_query("SELECT * FROM STUDENTS")
        st.dataframe(df_all, use_container_width=True)

# ------------------------------------------------------------------------------
# 5. Main Text-to-SQL Query Interface
# ------------------------------------------------------------------------------
st.markdown("### 💬 Ask QueryMind AI to Query Your Database")

# Example Prompt Chips
st.markdown("**Try asking:**")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📊 Show top 5 students in Data Science"):
        st.session_state["user_query"] = "Show the top 5 students in Data Science ordered by marks"
with col2:
    if st.button("📈 Average marks by Class"):
        st.session_state["user_query"] = "What is the average mark for each class?"
with col3:
    if st.button("🏆 List students with A+ Grade"):
        st.session_state["user_query"] = "List all students who scored an A+ grade"

# Input Box
default_prompt = st.session_state.get("user_query", "")
user_prompt = st.text_input(
    "Enter your natural language prompt:",
    value=default_prompt,
    placeholder="e.g., How many students are in Cybersecurity with marks over 80?"
)

if st.button("🚀 Generate & Execute SQL", type="primary", use_container_width=True):
    if not user_prompt.strip():
        st.warning("Please enter a question or select an example prompt.")
    else:
        with st.spinner("Analyzing database schema and generating SQL..."):
            # System instruction instructing Gemini to act strictly as a Text-to-SQL agent
            system_instruction = f"""
            You are QueryMind AI, an expert SQL generator.
            Your job is to convert natural language questions into valid, executable SQLite queries based ONLY on the provided schema.
            
            DATABASE SCHEMA:
            {schema_text}
            
            RULES:
            1. Output ONLY the raw SQL query. Do not wrap in markdown code fences (no ```sql or ```).
            2. Do not include any introductory or concluding text in your main output.
            3. Ensure table and column names match the schema exactly.
            """

            try:
                # Call Gemini API
                response = client.models.generate_content(
                    model=selected_model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,  # Low temperature for precise SQL generation
                    )
                )

                # Clean generated SQL query
                generated_sql = response.text.strip().replace("```sql", "").replace("```", "").strip()

                # Display Generated SQL
                st.markdown("#### 📝 Generated SQL Query")
                st.code(generated_sql, language="sql")

                # Execute SQL query against SQLite database
                df_result, error = execute_sql_query(generated_sql)

                if error:
                    st.error(f"❌ SQL Execution Error: {error}")
                else:
                    st.markdown("#### 📊 Execution Results")
                    if df_result.empty:
                        st.info("Query executed successfully, but returned 0 rows.")
                    else:
                        st.dataframe(df_result, use_container_width=True)

                        # Automatic Visualization for numerical data
                        numeric_cols = df_result.select_dtypes(include=["number"]).columns.tolist()
                        categorical_cols = df_result.select_dtypes(include=["object"]).columns.tolist()

                        if len(numeric_cols) > 0 and len(categorical_cols) > 0:
                            st.markdown("#### 📈 Data Visualization")
                            fig = px.bar(
                                df_result,
                                x=categorical_cols[0],
                                y=numeric_cols[0],
                                color=categorical_cols[0],
                                title=f"{numeric_cols[0]} by {categorical_cols[0]}"
                            )
                            st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred while connecting to Gemini: {e}")