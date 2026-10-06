# 🧠 QueryMind AI — Local Text-to-SQL Assistant

QueryMind AI is a Streamlit-based dashboard that transforms natural language questions into executable SQLite queries, fetches data, and automatically generates interactive Plotly visualizations—powered **100% locally** using Ollama.

---

## ✨ Features

- **🔒 100% Offline & Private:** Powered locally by Ollama. No external API keys or cloud dependencies.
- **💬 Natural Language to SQL:** Translates plain English prompts directly into valid SQLite queries.
- **📊 Instant Data Visualizations:** Automatically generates interactive Plotly charts for numeric data results.
- **🗄️ Built-in Database Schema Viewer:** Inspect table structures and view raw database records directly in the sidebar.
- **🛡️ Clean Query Guardrails:** Enforces clean SQL execution by filtering internal SQLite metadata (`sqlite_sequence`) out of model prompts.

---

## 🛠️ Tech Stack

- **Frontend / UI:** Streamlit
- **LLM Engine:** Ollama (`qwen2.5-coder`, `llama3.2`, etc.)
- **Database:** SQLite
- **Data Analysis & Visualization:** Pandas, Plotly Express

---

## 🚀 Getting Started

### 1. Prerequisites

Make sure you have [Ollama](https://ollama.com) installed and running on your machine.

Pull your preferred model for SQL generation (we recommend `qwen2.5-coder:7b` or `llama3.2`):

```bash
ollama pull qwen2.5-coder:7b
