"""
DataPulse Backend - FastAPI Application
========================================

API REST per l'analisi dati aziendali con generazione SQL tramite AI.

Questo modulo fornisce:
- Endpoint /api/analyze per interrogare dati con linguaggio naturale
- Integrazione con Google Gemini per generazione SQL
- Validazione sicurezza SQL con whitelist tabelle
- Cache e rate limiting per ottimizzazione performance

Author: Luca Neviani
Version: 1.0.0
License: MIT
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from backend.models import create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from backend.ai_service import (
    generate_sql, validate_sql, validate_sql_strict, 
    get_cache_stats, clear_cache, sanitize_input, ALLOWED_TABLES
)

# ============================================================================
# CONFIGURAZIONE LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("datapulse")

# ============================================================================
# MODELLI PYDANTIC (Request/Response)
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Schema richiesta per endpoint /api/analyze."""
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        description="Domanda in linguaggio naturale (es. 'Quanti clienti ci sono?')",
        examples=["How many customers are there?", "What are the total sales by region?"]
    )

class AnalyzeResponse(BaseModel):
    """Schema risposta successo per endpoint /api/analyze."""
    generated_sql: str = Field(..., description="Query SQL generata dall'AI")
    data: List[Dict[str, Any]] = Field(..., description="Risultati della query")
    row_count: int = Field(0, description="Numero di righe restituite")

class ErrorResponse(BaseModel):
    """Schema risposta errore."""
    error: str = Field(..., description="Messaggio di errore")
    generated_sql: Optional[str] = Field(None, description="SQL generato (se disponibile)")
    suggestion: Optional[str] = Field(None, description="Suggerimento per risolvere l'errore")

# ============================================================================
# INIZIALIZZAZIONE APP FASTAPI
# ============================================================================

app = FastAPI(
    title="DataPulse API",
    description="""
## 📊 DataPulse - AI-Powered Business Intelligence

API REST per interrogare database SQL usando linguaggio naturale.

### Funzionalità:
- **Generazione SQL con AI** - Converti domande in query SQL sicure
- **Validazione Sicurezza** - Whitelist tabelle, blocco injection
- **Cache Intelligente** - Ottimizzazione performance
- **Rate Limiting** - Protezione API key

### Tabelle Disponibili:
- `customers` - Anagrafica clienti
- `products` - Catalogo prodotti  
- `orders` - Ordini
- `order_items` - Dettaglio ordini
    """,
    version="1.0.0",
    contact={
        "name": "Luca Neviani",
        "url": "https://github.com/lucaneviani/Datapulse"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# CORS Middleware per frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica i domini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONFIGURAZIONE DATABASE
# ============================================================================

engine = create_database()
Session = sessionmaker(bind=engine)

# Schema DB per AI (formato semplificato per prompt)
db_schema = """
customers(id, name, segment, country, city, state, postal_code, region)
products(id, name, category, sub_category)
orders(id, customer_id, order_date, ship_date, ship_mode, total)
order_items(id, order_id, product_id, quantity, sales, discount, profit)
"""

# Limite massimo righe restituite (protezione memoria)
MAX_ROWS = 1000


# ============================================================================
# ENDPOINTS API
# ============================================================================

@app.get("/health", tags=["System"])
def health_check():
    """
    Health check del server.
    
    Verifica che il servizio sia attivo e funzionante.
    
    Returns:
        dict: Status del servizio
    """
    return {"status": "healthy", "service": "DataPulse API", "version": "1.0.0"}


@app.get("/api/cache/stats", tags=["Cache"])
def cache_stats():
    """
    Statistiche cache SQL.
    
    Restituisce informazioni sulla cache delle query SQL generate.
    
    Returns:
        dict: size, max_size, ttl_seconds
    """
    return get_cache_stats()


@app.post("/api/cache/clear", tags=["Cache"])
def cache_clear():
    """
    Svuota la cache SQL.
    
    Rimuove tutte le query memorizzate nella cache.
    
    Returns:
        dict: Messaggio di conferma
    """
    clear_cache()
    return {"message": "Cache svuotata con successo"}


@app.get("/api/schema/tables", tags=["Schema"])
def get_allowed_tables():
    """
    Lista tabelle permesse.
    
    Restituisce l'elenco delle tabelle accessibili tramite l'API.
    
    Returns:
        dict: Lista delle tabelle nella whitelist
    """
    return {"allowed_tables": list(ALLOWED_TABLES)}


@app.post("/api/analyze", tags=["Analysis"], response_model=None)
def analyze(data: dict):
    """
    Analizza una domanda in linguaggio naturale.
    
    Questo endpoint:
    1. Sanitizza l'input dell'utente (protezione XSS/injection)
    2. Genera SQL tramite AI (Google Gemini)
    3. Valida la sicurezza della query (whitelist tabelle, blocco operazioni pericolose)
    4. Esegue la query sul database
    5. Restituisce i risultati in formato JSON
    
    Args:
        data: dict con chiave "question" contenente la domanda
    
    Returns:
        - Successo: {"generated_sql": str, "data": list, "row_count": int}
        - Errore: {"error": str, "generated_sql": str|None, "suggestion": str|None}
    
    Examples:
        >>> {"question": "How many customers are there?"}
        {"generated_sql": "SELECT COUNT(*) FROM customers;", "data": [{"COUNT(*)": 793}], "row_count": 1}
    """
    raw_question = data.get("question", "")
    
    # Sanitizza input
    question = sanitize_input(raw_question)
    
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
    
    # Valida sicurezza SQL con validazione strict
    is_valid, error_msg = validate_sql_strict(sql)
    if not is_valid:
        logger.warning(f"SQL non sicuro generato: {sql[:100]} - Motivo: {error_msg}")
        return {
            "error": f"La query generata non è sicura: {error_msg}",
            "generated_sql": sql,
            "suggestion": "Prova a riformulare la domanda in modo più specifico"
        }
    
    logger.info(f"SQL generato e validato: {sql[:100]}...")
    
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
