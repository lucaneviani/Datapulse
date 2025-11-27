import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-exp") 

def generate_sql(question, db_schema):
    prompt = f"""
You are an expert SQL query generator for a business intelligence application called DataPulse.
Your task is to generate a valid, safe SELECT SQL query based on the user's natural language question.
Use only the provided database schema. Do not use any tables or columns not listed.
Always generate only SELECT queries – never INSERT, UPDATE, DELETE, DROP, or any other operations.
Ensure the query is syntactically correct for SQLite.

Database Schema:
{db_schema}

Instructions:
- Respond with ONLY the SQL query, no explanations or extra text.
- Use proper SQL syntax, including JOINs if needed for related tables.
- For aggregations (counts, sums), use appropriate functions.
- If the question cannot be answered with the schema, return a simple SELECT from a relevant table.

Example 1:
Question: "How many customers are there?"
SQL: SELECT COUNT(*) FROM customers;

Example 2:
Question: "What are the total sales by region?"
SQL: SELECT region, SUM(total) FROM orders JOIN customers ON orders.customer_id = customers.id GROUP BY region;

Question: {question}
SQL:
"""
    try:
        response = model.generate_content(prompt)
        sql = response.text.strip()
        # Rimuovi markdown se presente
        if sql.startswith("```sql"):
            sql = sql[6:].strip()
        if sql.endswith("```"):
            sql = sql[:-3].strip()
        return sql
    except Exception as e:
        return f"Error: {str(e)}"

def validate_sql(sql):
    if not sql or not isinstance(sql, str):
        return False
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT"):
        return False
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    for word in forbidden:
        if word in sql_upper:
            return False
    return True