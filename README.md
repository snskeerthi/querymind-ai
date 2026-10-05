# QueryMind AI — Natural Language Database Analytics & BI Dashboard

QueryMind AI is a self-service Business Intelligence (BI) tool built with Streamlit, Python, SQLite, and Google Gemini API. It allows users to ask plain-English questions about database metrics, translates them into executable SQL queries, runs the analysis, and renders interactive charts.

## Features
- **Natural Language to SQL:** Translates free-text prompts into precise SQLite queries using `gemini-2.5-flash`.
- **Zero Database Setup:** Uses an in-memory SQLite database populated with business metrics.
- **Dynamic Data Visualization:** Automatically generates Plotly charts based on returning DataFrame structures.
- **Schema Awareness:** Automatically extracts and feeds active table schemas into the model prompt context.

## Local Setup
1. Clone repository & set up environment:
   ```bash
   git clone <your-repo-url>
   cd querymind-ai
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt