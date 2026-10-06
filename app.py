import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import ollama

# ------------------------------------------------------------------------------
# 1. Streamlit Page Config & Title
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="QueryMind AI - Local Text-to-SQL",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧠 QueryMind AI — Local Text-to-SQL Assistant")
st.caption("Powered 100% locally with Ollama. Zero API keys, completely private.")

# ------------------------------------------------------------------------------
# 2. Database Setup (Sample SQLite DB)
# ------------------------------------------------------------------------------
DB_FILE = "student_data.db"

def init_sample_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
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

def get_db_schema():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Filter out internal SQLite tables from schema string sent to LLM
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
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

def execute_sql_query(sql_query):
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df, None
    except Exception as e:
        conn.close()
        return None, str(e)

# Fetch available Ollama models dynamically
def get_installed_ollama_models():
    try:
        models_response = ollama.list()
        return [m.model for m in models_response.models]
    except Exception:
        return []

installed_models = get_installed_ollama_models()

# ------------------------------------------------------------------------------
# 3. Sidebar Configuration
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🦙 Ollama Local Engine")
    
    if installed_models:
        selected_model = st.selectbox(
            "Select Local Model",
            installed_models,
            index=0
        )
        st.success("🟢 Ollama Connected")
    else:
        st.error("🔴 Ollama connection failed or no models pulled.")
        st.info("Make sure Ollama app is running and execute `ollama pull qwen2.5-coder:7b` in terminal.")
        selected_model = None

    st.markdown("---")
    st.markdown("## 🗄️️ Database Schema")
    schema_text = get_db_schema()
    st.code(schema_text, language="sql")
    
    if st.button("👁️ View Full Database Table"):
        df_all, _ = execute_sql_query("SELECT * FROM STUDENTS")
        st.dataframe(df_all, use_container_width=True)

# ------------------------------------------------------------------------------
# 4. Main QueryMind Interface
# ------------------------------------------------------------------------------
st.markdown("### 💬 Ask QueryMind AI to Query Your Database")

st.markdown("**Try asking:**")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📊 Top 5 students in Data Science"):
        st.session_state["user_query"] = "Show the top 5 students in Data Science ordered by marks"
with col2:
    if st.button("📈 Average marks by Class"):
        st.session_state["user_query"] = "What is the average mark for each class?"
with col3:
    if st.button("🏆 List students with A+ Grade"):
        st.session_state["user_query"] = "List all students who scored an A+ grade"

default_prompt = st.session_state.get("user_query", "")
user_prompt = st.text_input(
    "Enter your natural language prompt:",
    value=default_prompt,
    placeholder="e.g., How many students are in Cybersecurity with marks over 80?"
)

if st.button("🚀 Generate & Execute SQL", type="primary", use_container_width=True):
    if not selected_model:
        st.error("Please start Ollama service and select a model in the sidebar.")
    elif not user_prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner(f"Generating SQL locally using `{selected_model}`..."):
            prompt_content = f"""
            You are an expert SQL generator for SQLite.
            Convert the following question into a valid, executable SQLite query based ONLY on the provided schema.

            DATABASE SCHEMA:
            {schema_text}

            QUESTION: {user_prompt}

            STRICT RULES:
            1. Output ONLY the raw SQL query.
            2. Do NOT wrap in markdown fences (no ```sql or ```) or include extra commentary text.
            3. Query ONLY the user tables provided in the schema (e.g., STUDENTS).
            4. NEVER join or reference internal SQLite tables like sqlite_sequence, sqlite_master, etc.
            5. Ensure column and table names match the schema exactly.
            """

            try:
                # Call local Ollama model
                response = ollama.generate(
                    model=selected_model,
                    prompt=prompt_content,
                    options={"temperature": 0.1}
                )

                raw_sql = response["response"].strip()
                generated_sql = raw_sql.replace("```sql", "").replace("```", "").strip()

                st.markdown("#### 📝 Generated SQL Query")
                st.code(generated_sql, language="sql")

                # Execute SQL
                df_result, error = execute_sql_query(generated_sql)

                if error:
                    st.error(f"❌ SQL Execution Error: {error}")
                else:
                    st.markdown("#### 📊 Execution Results")
                    if df_result.empty:
                        st.info("Query executed successfully, but returned 0 rows.")
                    else:
                        st.dataframe(df_result, use_container_width=True)

                        # Automatic Plotly Chart
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
                st.error(f"Error communicating with local Ollama service: {e}")
