"""
DataPulse API Server

FastAPI application providing REST endpoints for natural language to SQL
conversion powered by Google Gemini AI.

Endpoints:
    POST /api/analyze     - Convert natural language to SQL and execute
    POST /api/upload/*    - Upload custom databases (CSV, Excel, SQLite)
    POST /api/auth/*      - User authentication (JWT)
    POST /api/export/*    - Export data (PDF, Excel, CSV, HTML)
    GET  /api/dashboard/* - Dashboard management

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from typing import Optional, List, Dict, Any
from backend.models import create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from backend.ai_service import (
    generate_sql, validate_sql, validate_sql_strict, validate_sql_dynamic,
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

# B3: Import centralized Pydantic schemas
from backend.schemas import (
    AnalyzeRequest, AnalyzeResponse, ErrorResponse,
    RegisterRequest, LoginRequest, AuthResponse,
    ExportRequest, ExportResponse,
    DashboardCreateRequest, DashboardResponse,
    SessionCreateResponse, SchemaResponse, HealthCheckResponse,
    AnalyzeSessionRequest
)

# B5: Import error handling middleware
from backend.middleware import (
    setup_middleware,
    DataPulseException, ValidationException, NotFoundException,
    DatabaseException, AIServiceException, RateLimitException,
    get_request_id
)

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("datapulse")

# NOTE: Request/Response models are now imported from backend.schemas (B3 refactoring)
# See: backend/schemas.py for all Pydantic models

# -----------------------------------------------------------------------------
# Application Lifespan (startup/shutdown)
# -----------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("DataPulse API Starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Debug Mode: {os.getenv('DEBUG', 'false')}")
    
    # Validate configuration
    try:
        from backend.config import settings, validate_settings
        warnings = validate_settings()
        for warning in warnings:
            logger.warning(f"Config: {warning}")
    except ImportError:
        pass
    
    logger.info("DataPulse API Ready ✓")
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("DataPulse API Shutting down...")
    
    # Clear sensitive data from cache
    try:
        clear_cache()
        logger.info("Cache cleared")
    except Exception as e:
        logger.warning(f"Cache clear failed: {e}")
    
    # Session cleanup is handled by SessionManager's background thread
    logger.info("DataPulse API Stopped")

# -----------------------------------------------------------------------------
# FastAPI Application
# -----------------------------------------------------------------------------

app = FastAPI(
    title="DataPulse API",
    description="""
## DataPulse - AI-Powered Business Intelligence

REST API for querying SQL databases using natural language.

### Features:
- **AI SQL Generation** - Convert questions to secure SQL queries
- **Security Validation** - Table whitelist, injection protection
- **Smart Caching** - Performance optimization
- **Rate Limiting** - API key protection

### Available Tables:
- `customers` - Customer records
- `products` - Product catalog
- `orders` - Orders
- `order_items` - Order details
    """,
    version="2.1.0",
    contact={
        "name": "Luca Neviani",
        "url": "https://github.com/lucaneviani/Datapulse"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

# CORS Middleware for frontend
# SECURITY: In production, ALWAYS set CORS_ORIGINS env var!
# Example: CORS_ORIGINS=https://myapp.com,https://admin.myapp.com
_cors_origins = os.getenv("CORS_ORIGINS", "")
if not _cors_origins:
    # Development mode: allow localhost only
    ALLOWED_ORIGINS = ["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000"]
    logger.warning("CORS_ORIGINS not set - using localhost defaults. Set CORS_ORIGINS in production!")
elif _cors_origins == "*":
    ALLOWED_ORIGINS = ["*"]
    logger.warning("CORS_ORIGINS='*' is insecure for production!")
else:
    ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# B5: Setup error handling middleware
setup_middleware(app, debug=os.getenv("DEBUG", "false").lower() == "true")

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

engine = create_database()
Session = sessionmaker(bind=engine)

# Database schema for AI prompt (simplified format)
db_schema = """
customers(id, name, segment, country, city, state, postal_code, region)
products(id, name, category, sub_category)
orders(id, customer_id, order_date, ship_date, ship_mode, total)
order_items(id, order_id, product_id, quantity, sales, discount, profit)
"""

# Maximum rows returned (memory protection)
MAX_ROWS = 1000


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def health_check():
    """
    Comprehensive health check endpoint for production monitoring.
    
    Checks:
        - Database connectivity
        - AI service availability
        - Cache status
        - System readiness
    
    Returns:
        dict: Detailed service status for load balancers and monitoring
    """
    import time
    from datetime import datetime, timezone
    
    start_time = time.time()
    checks = {}
    overall_status = "healthy"
    
    # Database check
    try:
        with Session() as session:
            session.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)[:100]}
        overall_status = "degraded"
    
    # AI service check
    try:
        from backend.ai_service import model
        if model is not None:
            checks["ai_service"] = {"status": "healthy", "model": "gemini-2.0-flash-exp"}
        else:
            checks["ai_service"] = {"status": "degraded", "error": "API key not configured"}
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        checks["ai_service"] = {"status": "unhealthy", "error": str(e)[:100]}
        overall_status = "degraded"
    
    # Cache check
    try:
        cache_info = get_cache_stats()
        checks["cache"] = {
            "status": "healthy",
            "size": cache_info.get("size", 0),
            "max_size": cache_info.get("max_size", 100)
        }
    except Exception as e:
        checks["cache"] = {"status": "degraded", "error": str(e)[:50]}
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "DataPulse API",
        "version": "2.1.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "response_time_ms": response_time,
        "checks": checks
    }


@app.get("/api/cache/stats", tags=["Cache"])
def cache_stats():
    """
    Get SQL cache statistics.
    
    Returns:
        dict: Cache size, max_size, ttl_seconds
    """
    return get_cache_stats()


@app.post("/api/cache/clear", tags=["Cache"])
def cache_clear():
    """
    Clear the SQL cache.
    
    Returns:
        dict: Confirmation message
    """
    clear_cache()
    return {"message": "Cache cleared successfully"}


@app.get("/api/schema/tables", tags=["Schema"])
def get_allowed_tables():
    """
    Get list of allowed tables.
    
    Returns:
        dict: List of tables in the whitelist
    """
    return {"allowed_tables": list(ALLOWED_TABLES)}


@app.post("/api/analyze", tags=["Analysis"], response_model=None)
def analyze(request: AnalyzeRequest):
    """
    Analyze a natural language question.
    
    This endpoint:
    1. Sanitizes user input (XSS/injection protection)
    2. Generates SQL via AI (Google Gemini)
    3. Validates query security (table whitelist, blocks dangerous operations)
    4. Executes the query on the database
    5. Returns results in JSON format
    
    Args:
        request: AnalyzeRequest with question field
    
    Returns:
        Success: {"generated_sql": str, "data": list, "row_count": int}
        Error: {"error": str, "generated_sql": str|None, "suggestion": str|None}
    """
    raw_question = request.question
    
    # Sanitize input
    question = sanitize_input(raw_question)
    
    # Input validation
    if not question:
        logger.warning("Empty question received")
        return {
            "error": "Question cannot be empty",
            "generated_sql": None,
            "suggestion": "Try a question like 'How many customers are there?'"
        }
    
    if len(question) > 500:
        logger.warning(f"Question too long: {len(question)} characters")
        return {
            "error": "Question is too long (max 500 characters)",
            "generated_sql": None
        }
    
    logger.info(f"Processing question: {question[:50]}...")
    
    # Generate SQL with AI
    try:
        sql = generate_sql(question, db_schema)
    except Exception as e:
        logger.error(f"SQL generation error: {str(e)}")
        return {
            "error": "Error generating SQL query",
            "generated_sql": None,
            "suggestion": "Verify that the API key is configured correctly"
        }
    
    # Validate SQL security with strict validation
    is_valid, error_msg = validate_sql_strict(sql)
    if not is_valid:
        logger.warning(f"Unsafe SQL generated: {sql[:100]} - Reason: {error_msg}")
        return {
            "error": f"Generated query is not secure: {error_msg}",
            "generated_sql": sql,
            "suggestion": "Try rephrasing the question more specifically"
        }
    
    logger.info(f"SQL generated and validated: {sql[:100]}...")
    
    # Execute query with context manager to prevent session leaks
    try:
        with Session() as session:
            result = session.execute(text(sql)).mappings().all()
            
            # Limit rows
            if len(result) > MAX_ROWS:
                logger.info(f"Results truncated from {len(result)} to {MAX_ROWS}")
                result = result[:MAX_ROWS]
            
            # Convert results to list of dicts for JSON serialization
            data_list = [dict(row) for row in result]
            
            logger.info(f"Query executed successfully: {len(data_list)} rows")
            
            return {
                "generated_sql": sql,
                "data": data_list,
                "row_count": len(data_list)
            }
    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        return {
            "error": f"Error executing query: {str(e)}",
            "generated_sql": sql,
            "suggestion": "The query may reference non-existent tables or columns"
        }


# -----------------------------------------------------------------------------
# Session and Custom Database Endpoints
# -----------------------------------------------------------------------------

@app.post("/api/session/create", tags=["Session"])
def create_session():
    """
    Create a new user session.
    
    Each session has its own database (initially the demo database).
    
    Returns:
        dict: session_id, db_type, tables
    """
    session_id = session_manager.create_session()
    session = session_manager.get_session(session_id)
    
    return {
        "session_id": session_id,
        "db_type": session["db_type"],
        "tables": session["tables"],
        "message": "Session created with demo database"
    }


@app.get("/api/session/{session_id}/info", tags=["Session"])
def get_session_info(session_id: str):
    """
    Get session information.
    
    Args:
        session_id: Session ID
    
    Returns:
        dict: Session information
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
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
    Upload CSV/Excel files and create a custom database.
    
    Accepts .csv, .xlsx, .xls files
    
    Args:
        session_id: Session ID
        files: List of files to upload
    
    Returns:
        dict: Operation result
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Validate files
    allowed_extensions = {'.csv', '.xlsx', '.xls'}
    file_data = []
    
    for file in files:
        ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file.filename}. Use CSV or Excel."
            )
        
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50 MB
            raise HTTPException(status_code=400, detail=f"File too large: {file.filename}")
        
        file_data.append((file.filename, content))
    
    # Process files
    success, message = session_manager.upload_csv(session_id, file_data)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Get updated info
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
    Upload an existing SQLite database.
    
    Accepts .db, .sqlite, .sqlite3 files
    
    Args:
        session_id: Session ID
        file: Database file to upload
    
    Returns:
        dict: Operation result
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Validate file
    allowed_extensions = {'.db', '.sqlite', '.sqlite3'}
    ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Use .db, .sqlite or .sqlite3"
        )
    
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB
        raise HTTPException(status_code=400, detail="File too large (max 50 MB)")
    
    # Process file
    success, message = session_manager.upload_sqlite(session_id, file.filename, content)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Get updated info
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
    Reset session to the demo database.
    
    Args:
        session_id: Session ID
    
    Returns:
        dict: Operation result
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
    Analyze a question using the session's database.
    
    This endpoint uses the custom database uploaded by the user,
    or the demo database if no file was uploaded.
    
    Args:
        session_id: Session ID
        data: dict with "question" key
    
    Returns:
        Analysis result or error
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    raw_question = data.get("question", "")
    question = sanitize_input(raw_question)
    
    if not question:
        return {
            "error": "Question cannot be empty",
            "generated_sql": None,
            "suggestion": "Try asking a question about your data"
        }
    
    if len(question) > 500:
        return {
            "error": "Question is too long (max 500 characters)",
            "generated_sql": None
        }
    
    logger.info(f"[Session {session_id[:8]}] Processing question: {question[:50]}...")
    
    # Generate SQL with dynamic schema
    try:
        sql = generate_sql_dynamic(question, session["schema"], session["tables"])
    except Exception as e:
        logger.error(f"SQL generation error: {str(e)}")
        return {
            "error": "Error generating SQL query",
            "generated_sql": None,
            "suggestion": "Verify that the API key is configured correctly"
        }
    
    # If the generator returned an explicit error message, surface it clearly
    if isinstance(sql, str) and sql.lower().startswith("error:"):
        logger.warning(f"[Session {session_id[:8]}] SQL generation error returned: {sql}")
        return {
            "error": sql[6:].strip(),
            "generated_sql": None,
            "suggestion": "If AI is not configured, a fallback SQL generator will be used; otherwise, review the question or set GOOGLE_API_KEY in .env"
        }

    # Security validation for dynamic databases (without table whitelist)
    is_valid, error_msg = validate_sql_dynamic(sql)
    if not is_valid:
        logger.warning(f"[Session {session_id[:8]}] Unsafe SQL blocked: {error_msg}")
        return {
            "error": f"Query not allowed: {error_msg}",
            "generated_sql": sql,
            "suggestion": "Rephrase the question to retrieve data only"
        }
    
    logger.info(f"SQL generated: {sql[:100]}...")
    
    # Execute query on session database
    success, result = execute_query_on_session(session_id, sql, MAX_ROWS)
    
    if not success:
        return {
            "error": f"Error executing query: {result}",
            "generated_sql": sql,
            "suggestion": "The query may reference non-existent tables or columns"
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
def analyze_for_dashboard(data: DashboardCreateRequest):
    """
    Analyze data and suggest visualizations.
    
    Args:
        data: Data to analyze
    
    Returns:
        dict: Data analysis and chart suggestions
    """
    if not data.data:
        raise HTTPException(status_code=400, detail="No data provided")
    
    analysis = dashboard_manager.analyze_data(data.data)
    suggestions = dashboard_manager.suggest_visualizations(data.data, analysis)
    
    return {
        "analysis": analysis,
        "suggested_visualizations": suggestions
    }


@app.post("/api/dashboard/create", tags=["Dashboard"])
def create_dashboard(data: DashboardCreateRequest):
    """
    Create an automatic dashboard from data.
    
    Args:
        data: Data and title
    
    Returns:
        dict: Dashboard layout with widgets
    """
    if not data.data:
        raise HTTPException(status_code=400, detail="No data provided")
    
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
        raise HTTPException(status_code=400, detail="No data provided for report")
    
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
