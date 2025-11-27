from fastapi import FastAPI
from backend.models import create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from backend.ai_service import generate_sql, validate_sql

app = FastAPI()

# Connessione DB
engine = create_database()
Session = sessionmaker(bind=engine)

# Schema DB per AI
db_schema = """
customers(id, name, segment, country, city, state, postal_code, region)
products(id, name, category, sub_category)
orders(id, customer_id, order_date, ship_date, ship_mode, total)
order_items(id, order_id, product_id, quantity, sales, discount, profit)
"""

@app.post("/api/analyze")
def analyze(data: dict):
    question = data.get("question", "")
    # Genera SQL con AI
    sql = generate_sql(question, db_schema)
    if not validate_sql(sql):
        return {"error": "Generated SQL is not safe", "generated_sql": sql}
    # Esegui query
    session = Session()
    try:
        result = session.execute(text(sql)).mappings().all()
        # Converti risultati in lista di dict per JSON serialization
        data_list = [dict(row) for row in result]
        return {"generated_sql": sql, "data": data_list}
    except Exception as e:
        return {"error": f"Query execution failed: {str(e)}", "generated_sql": sql}
    finally:
        session.close()
