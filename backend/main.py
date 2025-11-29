"""
DataPulse Backend - FastAPI Application
========================================

API REST per l'analisi dati aziendali con generazione SQL tramite AI.

Questo modulo fornisce:
- Endpoint /api/analyze per interrogare dati con linguaggio naturale
- Endpoint per upload di database CSV/Excel/SQLite personalizzati
- Sistema di autenticazione JWT
- Dashboard automatiche
- Export avanzato (PDF, Excel, CSV, HTML)
- Integrazione con Google Gemini per generazione SQL
- Validazione sicurezza SQL con whitelist tabelle
- Cache e rate limiting per ottimizzazione performance

Author: Luca Neviani
Version: 2.1.0
License: MIT
"""

import logging
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from backend.models import create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from backend.ai_service import (
    generate_sql, validate_sql, validate_sql_strict, 
    get_cache_stats, clear_cache, sanitize_input, ALLOWED_TABLES,
    generate_sql_dynamic
)
from backend.database_manager import (
    session_manager, execute_query_on_session, 
    get_session_tables, get_session_schema
)
from backend.auth import auth_manager
from backend.dashboard import dashboard_manager
from backend.export_service import export_service

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
# MODELLI AUTENTICAZIONE
# ============================================================================

class RegisterRequest(BaseModel):
    """Schema richiesta registrazione utente."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

class LoginRequest(BaseModel):
    """Schema richiesta login."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

class ExportRequest(BaseModel):
    """Schema richiesta export."""
    data: List[Dict[str, Any]] = Field(..., description="Dati da esportare")
    format: str = Field(..., description="Formato: pdf, excel, csv, html")
    title: Optional[str] = Field("Report DataPulse", description="Titolo del report")
    query: Optional[str] = Field(None, description="Query SQL eseguita")

class DashboardRequest(BaseModel):
    """Schema richiesta creazione dashboard."""
    data: List[Dict[str, Any]] = Field(..., description="Dati da analizzare")
    title: Optional[str] = Field("Dashboard", description="Titolo dashboard")

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


# ============================================================================
# ENDPOINTS SESSIONE E DATABASE PERSONALIZZATI
# ============================================================================

@app.post("/api/session/create", tags=["Session"])
def create_session():
    """
    Crea una nuova sessione utente.
    
    Ogni sessione ha il proprio database (inizialmente il demo).
    
    Returns:
        dict: session_id, db_type, tables
    """
    session_id = session_manager.create_session()
    session = session_manager.get_session(session_id)
    
    return {
        "session_id": session_id,
        "db_type": session["db_type"],
        "tables": session["tables"],
        "message": "Sessione creata con database demo"
    }


@app.get("/api/session/{session_id}/info", tags=["Session"])
def get_session_info(session_id: str):
    """
    Ottiene informazioni sulla sessione.
    
    Args:
        session_id: ID della sessione
    
    Returns:
        dict: Informazioni sulla sessione
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata o scaduta")
    
    return {
        "session_id": session_id,
        "db_type": session["db_type"],
        "tables": session["tables"],
        "schema": session["schema"]
    }


@app.post("/api/session/{session_id}/upload/csv", tags=["Upload"])
async def upload_csv_files(
    session_id: str,
    files: List[UploadFile] = File(...)
):
    """
    Carica file CSV/Excel e crea un database personalizzato.
    
    Accetta file .csv, .xlsx, .xls
    
    Args:
        session_id: ID della sessione
        files: Lista di file da caricare
    
    Returns:
        dict: Risultato dell'operazione
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata o scaduta")
    
    # Valida file
    allowed_extensions = {'.csv', '.xlsx', '.xls'}
    file_data = []
    
    for file in files:
        ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Formato file non supportato: {file.filename}. Usa CSV o Excel."
            )
        
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50 MB
            raise HTTPException(status_code=400, detail=f"File troppo grande: {file.filename}")
        
        file_data.append((file.filename, content))
    
    # Processa file
    success, message = session_manager.upload_csv(session_id, file_data)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Ottieni info aggiornate
    session = session_manager.get_session(session_id)
    
    return {
        "success": True,
        "message": message,
        "db_type": session["db_type"],
        "tables": session["tables"],
        "schema": session["schema"]
    }


@app.post("/api/session/{session_id}/upload/sqlite", tags=["Upload"])
async def upload_sqlite_file(
    session_id: str,
    file: UploadFile = File(...)
):
    """
    Carica un database SQLite esistente.
    
    Accetta file .db, .sqlite, .sqlite3
    
    Args:
        session_id: ID della sessione
        file: File database da caricare
    
    Returns:
        dict: Risultato dell'operazione
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata o scaduta")
    
    # Valida file
    allowed_extensions = {'.db', '.sqlite', '.sqlite3'}
    ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Formato file non supportato. Usa .db, .sqlite o .sqlite3"
        )
    
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB
        raise HTTPException(status_code=400, detail="File troppo grande (max 50 MB)")
    
    # Processa file
    success, message = session_manager.upload_sqlite(session_id, file.filename, content)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Ottieni info aggiornate
    session = session_manager.get_session(session_id)
    
    return {
        "success": True,
        "message": message,
        "db_type": session["db_type"],
        "tables": session["tables"],
        "schema": session["schema"]
    }


@app.post("/api/session/{session_id}/reset", tags=["Session"])
def reset_session_to_demo(session_id: str):
    """
    Resetta la sessione al database demo.
    
    Args:
        session_id: ID della sessione
    
    Returns:
        dict: Risultato dell'operazione
    """
    success, message = session_manager.reset_to_demo(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    session = session_manager.get_session(session_id)
    
    return {
        "success": True,
        "message": message,
        "db_type": session["db_type"],
        "tables": session["tables"]
    }


@app.post("/api/session/{session_id}/analyze", tags=["Analysis"])
def analyze_with_session(session_id: str, data: dict):
    """
    Analizza una domanda usando il database della sessione.
    
    Questo endpoint usa il database personalizzato caricato dall'utente,
    o il database demo se nessun file è stato caricato.
    
    Args:
        session_id: ID della sessione
        data: dict con chiave "question"
    
    Returns:
        Risultato dell'analisi o errore
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata o scaduta")
    
    raw_question = data.get("question", "")
    question = sanitize_input(raw_question)
    
    if not question:
        return {
            "error": "La domanda non può essere vuota",
            "generated_sql": None,
            "suggestion": "Prova con una domanda sui tuoi dati"
        }
    
    if len(question) > 500:
        return {
            "error": "La domanda è troppo lunga (max 500 caratteri)",
            "generated_sql": None
        }
    
    logger.info(f"[Session {session_id[:8]}] Elaborazione domanda: {question[:50]}...")
    
    # Genera SQL con schema dinamico
    try:
        sql = generate_sql_dynamic(question, session["schema"], session["tables"])
    except Exception as e:
        logger.error(f"Errore generazione SQL: {str(e)}")
        return {
            "error": "Errore durante la generazione della query SQL",
            "generated_sql": None,
            "suggestion": "Verifica che la chiave API sia configurata correttamente"
        }
    
    # Per database custom, non usiamo la validazione strict delle tabelle
    # ma solo controlli di base
    if "DROP" in sql.upper() or "DELETE" in sql.upper() or "INSERT" in sql.upper() or "UPDATE" in sql.upper():
        return {
            "error": "Query non permessa: solo SELECT è consentito",
            "generated_sql": sql,
            "suggestion": "Riformula la domanda per ottenere dati, non modificarli"
        }
    
    logger.info(f"SQL generato: {sql[:100]}...")
    
    # Esegui query sul database della sessione
    success, result = execute_query_on_session(session_id, sql, MAX_ROWS)
    
    if not success:
        return {
            "error": f"Errore nell'esecuzione della query: {result}",
            "generated_sql": sql,
            "suggestion": "La query potrebbe fare riferimento a tabelle o colonne inesistenti"
        }
    
    logger.info(f"Query eseguita con successo: {len(result)} righe")
    
    return {
        "generated_sql": sql,
        "data": result,
        "row_count": len(result)
    }


# ============================================================================
# ENDPOINTS AUTENTICAZIONE
# ============================================================================

@app.post("/api/auth/register", tags=["Authentication"])
def register_user(data: RegisterRequest):
    """
    Registra un nuovo utente.
    
    Args:
        data: username, email, password
    
    Returns:
        dict: Informazioni utente e token JWT
    """
    success, result = auth_manager.register_user(
        username=data.username,
        email=data.email,
        password=data.password
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@app.post("/api/auth/login", tags=["Authentication"])
def login_user(data: LoginRequest):
    """
    Login utente.
    
    Args:
        data: username, password
    
    Returns:
        dict: Token JWT e informazioni utente
    """
    success, result = auth_manager.login_user(
        username=data.username,
        password=data.password
    )
    
    if not success:
        raise HTTPException(status_code=401, detail=result)
    
    return result


@app.get("/api/auth/me", tags=["Authentication"])
def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Ottiene informazioni sull'utente corrente.
    
    Richiede header Authorization: Bearer <token>
    
    Returns:
        dict: Informazioni utente
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token non fornito")
    
    token = authorization.replace("Bearer ", "")
    user = auth_manager.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Token non valido o scaduto")
    
    return user


@app.post("/api/auth/logout", tags=["Authentication"])
def logout_user(authorization: Optional[str] = Header(None)):
    """
    Logout utente (invalida il token).
    
    Returns:
        dict: Messaggio di conferma
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        auth_manager.logout_user(token)
    
    return {"message": "Logout effettuato con successo"}


# ============================================================================
# ENDPOINTS DASHBOARD
# ============================================================================

@app.post("/api/dashboard/analyze", tags=["Dashboard"])
def analyze_for_dashboard(data: DashboardRequest):
    """
    Analizza i dati e suggerisce visualizzazioni.
    
    Args:
        data: Dati da analizzare
    
    Returns:
        dict: Analisi dei dati e suggerimenti grafici
    """
    if not data.data:
        raise HTTPException(status_code=400, detail="Nessun dato fornito")
    
    analysis = dashboard_manager.analyze_data(data.data)
    suggestions = dashboard_manager.suggest_visualizations(data.data, analysis)
    
    return {
        "analysis": analysis,
        "suggested_visualizations": suggestions
    }


@app.post("/api/dashboard/create", tags=["Dashboard"])
def create_dashboard(data: DashboardRequest):
    """
    Crea una dashboard automatica dai dati.
    
    Args:
        data: Dati e titolo
    
    Returns:
        dict: Layout dashboard con widget
    """
    if not data.data:
        raise HTTPException(status_code=400, detail="Nessun dato fornito")
    
    dashboard = dashboard_manager.create_dashboard(
        data=data.data,
        title=data.title or "Dashboard"
    )
    
    return dashboard.to_dict()


@app.get("/api/dashboard/{dashboard_id}", tags=["Dashboard"])
def get_dashboard(dashboard_id: str):
    """
    Carica una dashboard salvata.
    
    Args:
        dashboard_id: ID della dashboard
    
    Returns:
        dict: Layout dashboard
    """
    dashboard = dashboard_manager.load_dashboard(dashboard_id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard non trovata")
    
    return dashboard


@app.post("/api/dashboard/{dashboard_id}/save", tags=["Dashboard"])
def save_dashboard(dashboard_id: str, layout: dict):
    """
    Salva una dashboard.
    
    Args:
        dashboard_id: ID della dashboard
        layout: Layout da salvare
    
    Returns:
        dict: Conferma salvataggio
    """
    success = dashboard_manager.save_dashboard(dashboard_id, layout)
    
    if not success:
        raise HTTPException(status_code=500, detail="Errore nel salvataggio")
    
    return {"success": True, "dashboard_id": dashboard_id}


# ============================================================================
# ENDPOINTS EXPORT
# ============================================================================

@app.post("/api/export", tags=["Export"])
def export_data(data: ExportRequest):
    """
    Esporta i dati nel formato richiesto.
    
    Formati supportati: pdf, excel, csv, html
    
    Args:
        data: Dati, formato, titolo, query
    
    Returns:
        File nel formato richiesto
    """
    if not data.data:
        raise HTTPException(status_code=400, detail="Nessun dato da esportare")
    
    format_lower = data.format.lower()
    
    try:
        if format_lower == "pdf":
            content = export_service.export_to_pdf(
                data=data.data,
                title=data.title,
                query=data.query
            )
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="report.pdf"'}
            )
        
        elif format_lower == "excel":
            content = export_service.export_to_excel(
                data=data.data,
                title=data.title,
                query=data.query
            )
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="report.xlsx"'}
            )
        
        elif format_lower == "csv":
            content = export_service.export_to_csv(data.data)
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="report.csv"'}
            )
        
        elif format_lower == "html":
            content = export_service.export_to_html(
                data=data.data,
                title=data.title,
                query=data.query
            )
            return Response(
                content=content,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="report.html"'}
            )
        
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Formato non supportato: {data.format}. Usa: pdf, excel, csv, html"
            )
    
    except Exception as e:
        logger.error(f"Errore export: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore durante l'export: {str(e)}")


@app.post("/api/export/report", tags=["Export"])
def generate_report(data: dict):
    """
    Genera un report completo con analisi.
    
    Args:
        data: {
            "data": [...],
            "format": "pdf|excel|html",
            "title": "Titolo",
            "query": "SQL query",
            "include_charts": true,
            "include_summary": true
        }
    
    Returns:
        Report completo nel formato richiesto
    """
    report_data = data.get("data", [])
    format_type = data.get("format", "pdf").lower()
    title = data.get("title", "Report DataPulse")
    query = data.get("query")
    include_charts = data.get("include_charts", True)
    include_summary = data.get("include_summary", True)
    
    if not report_data:
        raise HTTPException(status_code=400, detail="Nessun dato per il report")
    
    try:
        content = export_service.generate_report(
            data=report_data,
            format_type=format_type,
            title=title,
            query=query,
            include_charts=include_charts,
            include_summary=include_summary
        )
        
        # Determina content type
        content_types = {
            "pdf": "application/pdf",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "html": "text/html"
        }
        
        extensions = {
            "pdf": "pdf",
            "excel": "xlsx",
            "html": "html"
        }
        
        return Response(
            content=content,
            media_type=content_types.get(format_type, "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="report.{extensions.get(format_type, "bin")}"'
            }
        )
    
    except Exception as e:
        logger.error(f"Errore generazione report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore durante la generazione: {str(e)}")
