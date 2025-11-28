"""
DataPulse Backend - FastAPI Application
========================================
API principale per l'analisi dati con generazione SQL tramite AI.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from backend.models import create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from backend.ai_service import generate_sql, validate_sql, get_cache_stats, clear_cache

# Configurazione Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("datapulse")

# Modello Request/Response per validazione
class AnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Domanda in linguaggio naturale")

class AnalyzeResponse(BaseModel):
    generated_sql: str
    data: List[Dict[str, Any]]
    row_count: int = 0

class ErrorResponse(BaseModel):
    error: str
    generated_sql: Optional[str] = None
    suggestion: Optional[str] = None

# Inizializzazione App
app = FastAPI(
    title="DataPulse API",
    description="API per analisi dati aziendali con generazione SQL tramite AI",
    version="1.0.0"
)

# CORS Middleware per frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica i domini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Limite massimo righe restituite
MAX_ROWS = 1000


@app.get("/health")
def health_check():
    """Endpoint per verificare lo stato del server."""
    return {"status": "healthy", "service": "DataPulse API"}


@app.get("/api/cache/stats")
def cache_stats():
    """Restituisce statistiche sulla cache SQL."""
    return get_cache_stats()


@app.post("/api/cache/clear")
def cache_clear():
    """Svuota la cache SQL."""
    clear_cache()
    return {"message": "Cache svuotata con successo"}


@app.post("/api/analyze")
def analyze(data: dict):
    """
    Analizza una domanda in linguaggio naturale e restituisce dati dal database.
    
    - Genera SQL tramite AI (Gemini)
    - Valida la sicurezza della query
    - Esegue la query e restituisce i risultati
    """
    question = data.get("question", "").strip()
    
    # Validazione input
    if not question:
        logger.warning("Ricevuta domanda vuota")
        return {
            "error": "La domanda non può essere vuota",
            "generated_sql": None,
            "suggestion": "Prova con una domanda come 'Quanti clienti ci sono?'"
        }
    
    if len(question) > 500:
        logger.warning(f"Domanda troppo lunga: {len(question)} caratteri")
        return {
            "error": "La domanda è troppo lunga (max 500 caratteri)",
            "generated_sql": None
        }
    
    logger.info(f"Elaborazione domanda: {question[:50]}...")
    
    # Genera SQL con AI
    try:
        sql = generate_sql(question, db_schema)
    except Exception as e:
        logger.error(f"Errore generazione SQL: {str(e)}")
        return {
            "error": "Errore durante la generazione della query SQL",
            "generated_sql": None,
            "suggestion": "Verifica che la chiave API sia configurata correttamente"
        }
    
    # Valida sicurezza SQL
    if not validate_sql(sql):
        logger.warning(f"SQL non sicuro generato: {sql[:100]}")
        return {
            "error": "La query generata non è sicura o non è valida",
            "generated_sql": sql,
            "suggestion": "Prova a riformulare la domanda in modo più specifico"
        }
    
    logger.info(f"SQL generato: {sql[:100]}...")
    
    # Esegui query
    session = Session()
    try:
        result = session.execute(text(sql)).mappings().all()
        
        # Limita numero di righe
        if len(result) > MAX_ROWS:
            logger.info(f"Risultati troncati da {len(result)} a {MAX_ROWS}")
            result = result[:MAX_ROWS]
        
        # Converti risultati in lista di dict per JSON serialization
        data_list = [dict(row) for row in result]
        
        logger.info(f"Query eseguita con successo: {len(data_list)} righe")
        
        return {
            "generated_sql": sql,
            "data": data_list,
            "row_count": len(data_list)
        }
        
    except Exception as e:
        logger.error(f"Errore esecuzione query: {str(e)}")
        return {
            "error": f"Errore nell'esecuzione della query: {str(e)}",
            "generated_sql": sql,
            "suggestion": "La query potrebbe fare riferimento a tabelle o colonne inesistenti"
        }
    finally:
        session.close()
