"""
DataPulse AI Service

Core service for SQL generation using artificial intelligence,
optimized for production performance and security.

Features:
    - SQL Generation: Converts natural language to SQL using Google Gemini AI
    - Smart Caching: LRU cache with TTL to reduce API calls and costs
    - Rate Limiting: Protection against abuse with configurable time windows
    - Security Validation: Table/column whitelist, SQL injection blocking

Components:
    - SQLCache: In-memory cache for generated SQL (100 entries max, 1h TTL)
    - RateLimiter: API request limiter (30 req/min default)
    - generate_sql(): Main function for SQL generation
    - validate_sql(): Structural query validation
    - validate_sql_strict(): Advanced security validation

Configuration:
    Requires GOOGLE_API_KEY environment variable in .env file

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import warnings
# Suppress deprecation warning - migration to google.genai planned
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    try:
        import google.generativeai as genai
    except Exception:
        genai = None
import os
import hashlib
import time
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Tuple
from functools import lru_cache
from datetime import datetime, timedelta

load_dotenv()

# Configurazione Logging
logger = logging.getLogger("datapulse.ai")

# Configurazione API
API_KEY = os.getenv("GOOGLE_API_KEY")
if genai is not None and API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
    except Exception as e:
        model = None
        logger.warning(f"Failed to configure Google generative AI: {e}")
elif genai is None:
    model = None
    logger.warning("google.generativeai package not installed - AI service disabled")
else:
    model = None
    logger.warning("GOOGLE_API_KEY non configurata - AI service disabilitato")

# -----------------------------------------------------------------------------
# SQL Query Cache
# -----------------------------------------------------------------------------

class SQLCache:
    """In-memory cache for generated SQL queries."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[str, datetime]] = {}
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def _hash_key(self, question: str, schema: str) -> str:
        """Generate hash key for cache lookup."""
        content = f"{question.lower().strip()}:{schema}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, question: str, schema: str) -> Optional[str]:
        """Retrieve SQL from cache if present and not expired."""
        key = self._hash_key(question, schema)
        if key in self.cache:
            sql, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                logger.info(f"Cache HIT: {question[:30]}...")
                return sql
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    def set(self, question: str, schema: str, sql: str):
        """Store SQL in cache."""
        # Clean cache if full
        if len(self.cache) >= self.max_size:
            self._cleanup()
        
        key = self._hash_key(question, schema)
        self.cache[key] = (sql, datetime.now())
        logger.info(f"Cache SET: {question[:30]}...")
    
    def _cleanup(self):
        """Remove oldest entries."""
        now = datetime.now()
        # Remove expired
        expired = [k for k, (_, ts) in self.cache.items() if now - ts >= self.ttl]
        for k in expired:
            del self.cache[k]
        
        # If still full, remove oldest
        if len(self.cache) >= self.max_size:
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            for k, _ in sorted_items[:len(self.cache) // 2]:
                del self.cache[k]


# Global cache instance
sql_cache = SQLCache(max_size=100, ttl_seconds=3600)  # 1 hour TTL

# -----------------------------------------------------------------------------
# Rate Limiting
# -----------------------------------------------------------------------------

class RateLimiter:
    """Simple rate limiter to protect the API."""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: list = []
    
    def can_proceed(self) -> bool:
        """Check if a new request can proceed."""
        now = time.time()
        # Remove old requests
        self.requests = [ts for ts in self.requests if now - ts < self.window]
        
        if len(self.requests) >= self.max_requests:
            logger.warning(f"Rate limit reached: {len(self.requests)}/{self.max_requests}")
            return False
        
        self.requests.append(now)
        return True
    
    def get_wait_time(self) -> float:
        """Calculate wait time if rate limited."""
        if not self.requests:
            return 0
        return max(0, self.window - (time.time() - self.requests[0]))


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=30, window_seconds=60)

# -----------------------------------------------------------------------------
# Security: Table and Column Whitelist
# -----------------------------------------------------------------------------

# Allowed tables in database
ALLOWED_TABLES = {
    "customers", "products", "orders", "order_items"
}

# Allowed columns per table
ALLOWED_COLUMNS = {
    "customers": {"id", "name", "segment", "country", "city", "state", "postal_code", "region"},
    "products": {"id", "name", "category", "sub_category"},
    "orders": {"id", "customer_id", "order_date", "ship_date", "ship_mode", "total"},
    "order_items": {"id", "order_id", "product_id", "quantity", "sales", "discount", "profit"}
}

# Common table aliases
TABLE_ALIASES = {
    "c": "customers",
    "p": "products", 
    "o": "orders",
    "oi": "order_items"
}

# -----------------------------------------------------------------------------
# Input Sanitization
# -----------------------------------------------------------------------------

def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially dangerous characters.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters
    import re
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Remove HTML/script tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Strip dangerous SQL characters from start/end
    text = text.strip(";'\"")
    
    return text.strip()


def validate_tables_in_sql(sql: str) -> bool:
    """
    Verify that SQL query only uses allowed tables.
    
    Args:
        sql: SQL query to verify
    
    Returns:
        True if all tables are allowed, False otherwise
    """
    import re
    sql_upper = sql.upper()
    
    # Pattern to find table names after FROM and JOIN
    table_pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(table_pattern, sql_upper)
    
    for table in matches:
        table_lower = table.lower()
        # Check if it's an allowed table or alias
        if table_lower not in ALLOWED_TABLES and table_lower not in TABLE_ALIASES:
            logger.warning(f"Disallowed table detected: {table}")
            return False
    
    return True


# -----------------------------------------------------------------------------
# Enhanced Schema for AI Prompts
# -----------------------------------------------------------------------------

ENHANCED_SCHEMA = """
Table: customers
- id: INTEGER PRIMARY KEY (unique customer identifier)
- name: TEXT (customer full name)
- segment: TEXT (market segment: 'Consumer', 'Corporate', 'Home Office')
- country: TEXT (customer country)
- city: TEXT (customer city)
- state: TEXT (customer state/region)
- postal_code: TEXT (postal code)
- region: TEXT (macro-region: 'West', 'East', 'Central', 'South')

Table: products
- id: INTEGER PRIMARY KEY (unique product identifier)
- name: TEXT (product name)
- category: TEXT (category: 'Technology', 'Furniture', 'Office Supplies')
- sub_category: TEXT (product sub-category)

Table: orders
- id: INTEGER PRIMARY KEY (unique order identifier)
- customer_id: INTEGER FOREIGN KEY -> customers.id
- order_date: DATE (data dell'ordine, formato YYYY-MM-DD)
- ship_date: DATE (data di spedizione)
- ship_mode: TEXT (modalità spedizione: 'Standard Class', 'Second Class', 'First Class', 'Same Day')
- total: REAL (totale ordine in €)

Table: order_items
- id: INTEGER PRIMARY KEY (identificatore univoco riga ordine)
- order_id: INTEGER FOREIGN KEY -> orders.id
- product_id: INTEGER FOREIGN KEY -> products.id
- quantity: INTEGER (quantità ordinata)
- sales: REAL (vendite in €)
- discount: REAL (sconto applicato, es. 0.2 = 20%)
- profit: REAL (profitto in €)

RELATIONSHIPS:
- orders.customer_id -> customers.id (ogni ordine appartiene a un cliente)
- order_items.order_id -> orders.id (ogni riga ordine appartiene a un ordine)
- order_items.product_id -> products.id (ogni riga ordine contiene un prodotto)
"""

# ============================================================================
# GENERAZIONE SQL
# ============================================================================

def generate_sql(question: str, db_schema: str = None) -> str:
    """
    Genera una query SQL sicura dalla domanda in linguaggio naturale.
    
    Args:
        question: Domanda in linguaggio naturale
        db_schema: Schema DB (opzionale, usa ENHANCED_SCHEMA se non fornito)
    
    Returns:
        Query SQL generata o messaggio di errore
    """
    if not question or not question.strip():
        return "Error: Domanda vuota"
    
    # Usa schema enhanced se non fornito
    schema = db_schema or ENHANCED_SCHEMA
    
    # Controlla cache
    cached_sql = sql_cache.get(question, schema)
    if cached_sql:
        return cached_sql
    
    # Controlla rate limiting
    if not rate_limiter.can_proceed():
        wait_time = rate_limiter.get_wait_time()
        return f"Error: Troppe richieste. Riprova tra {int(wait_time)} secondi."
    
    # Verifica API configurata
    if not model:
        return "Error: API key non configurata. Imposta GOOGLE_API_KEY nel file .env"
    
    # Prompt ottimizzato con più esempi e istruzioni dettagliate
    prompt = f"""You are an expert SQL query generator for DataPulse, a business intelligence application.
Generate a valid, safe SELECT SQL query based on the user's natural language question.

STRICT RULES:
1. Generate ONLY SELECT queries - never INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE
2. Use ONLY tables and columns from the schema below
3. Use proper SQLite syntax
4. Return ONLY the SQL query, no explanations or markdown
5. Use table aliases for readability (c for customers, p for products, o for orders, oi for order_items)
6. Always use explicit JOIN syntax, not implicit joins
7. For date filtering, use SQLite functions: strftime('%Y', date_column), date(date_column)

DATABASE SCHEMA:
{schema}

EXAMPLES:

Question: "How many customers are there?"
SQL: SELECT COUNT(*) as customer_count FROM customers;

Question: "What are the total sales by region?"
SQL: SELECT c.region, SUM(o.total) as total_sales FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.region ORDER BY total_sales DESC;

Question: "Show top 5 products by profit"
SQL: SELECT p.name, SUM(oi.profit) as total_profit FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id, p.name ORDER BY total_profit DESC LIMIT 5;

Question: "How many orders per month in 2023?"
SQL: SELECT strftime('%Y-%m', o.order_date) as month, COUNT(*) as order_count FROM orders o WHERE strftime('%Y', o.order_date) = '2023' GROUP BY month ORDER BY month;

Question: "Which customers spent more than 1000?"
SQL: SELECT c.name, SUM(o.total) as total_spent FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name HAVING total_spent > 1000 ORDER BY total_spent DESC;

Question: "Average order value by customer segment"
SQL: SELECT c.segment, AVG(o.total) as avg_order_value FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.segment;

Question: "Products in Technology category with their sales"
SQL: SELECT p.name, p.sub_category, SUM(oi.sales) as total_sales FROM products p JOIN order_items oi ON p.id = oi.product_id WHERE p.category = 'Technology' GROUP BY p.id, p.name, p.sub_category ORDER BY total_sales DESC;

Question: "Customers who never ordered"
SQL: SELECT c.name, c.region FROM customers c WHERE c.id NOT IN (SELECT DISTINCT customer_id FROM orders);

NOW GENERATE SQL FOR:
Question: "{question}"
SQL:"""

    try:
        logger.info(f"Generazione SQL per: {question[:50]}...")
        response = model.generate_content(prompt)
        sql = response.text.strip()
        
        # Rimuovi markdown se presente
        if sql.startswith("```sql"):
            sql = sql[6:].strip()
        if sql.startswith("```"):
            sql = sql[3:].strip()
        if sql.endswith("```"):
            sql = sql[:-3].strip()
        
        # Rimuovi newline multipli
        sql = " ".join(sql.split())
        
        # Salva in cache solo se valido
        if validate_sql(sql):
            sql_cache.set(question, schema, sql)
        
        logger.info(f"SQL generato: {sql[:80]}...")
        return sql
        
    except Exception as e:
        logger.error(f"Errore generazione SQL: {str(e)}")
        return f"Error: {str(e)}"


def validate_sql(sql: str, check_tables: bool = True) -> bool:
    """
    Valida che la query SQL sia sicura (solo SELECT, no operazioni pericolose).
    
    Args:
        sql: Query SQL da validare
        check_tables: Se True, verifica anche che le tabelle siano nella whitelist
    
    Returns:
        True se la query è sicura, False altrimenti
    """
    if not sql or not isinstance(sql, str):
        return False
    
    sql_upper = sql.upper().strip()
    
    # Deve iniziare con SELECT
    if not sql_upper.startswith("SELECT"):
        return False
    
    # Lista di parole chiave pericolose
    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
        "CREATE", "TRUNCATE", "EXEC", "EXECUTE", 
        "GRANT", "REVOKE", "COMMIT", "ROLLBACK",
        "ATTACH", "DETACH", "PRAGMA", "VACUUM",
        "REINDEX", "ANALYZE"  # SQLite specific
    ]
    
    for word in forbidden:
        # Cerca la parola come token separato (non parte di altra parola)
        if f" {word} " in f" {sql_upper} " or sql_upper.startswith(f"{word} "):
            return False
    
    # Blocca commenti SQL (possibile injection)
    if "--" in sql or "/*" in sql:
        return False
    
    # Blocca punto e virgola multipli (possibile injection multi-statement)
    if sql.count(";") > 1:
        return False
    
    # Blocca UNION (possibile injection per leggere altre tabelle)
    # Nota: UNION legittimo è raro in questo contesto
    if " UNION " in sql_upper:
        logger.warning("UNION rilevato e bloccato per sicurezza")
        return False
    
    # Verifica whitelist tabelle
    if check_tables and not validate_tables_in_sql(sql):
        return False
    
    return True


def validate_sql_strict(sql: str) -> tuple[bool, str]:
    """
    Validazione SQL rigorosa con messaggio di errore dettagliato.
    
    Args:
        sql: Query SQL da validare
    
    Returns:
        Tupla (is_valid, error_message)
    """
    if not sql or not isinstance(sql, str):
        return False, "Query SQL vuota o non valida"
    
    sql_upper = sql.upper().strip()
    
    if not sql_upper.startswith("SELECT"):
        return False, "Solo query SELECT sono permesse"
    
    # Controlli specifici con messaggi
    if "--" in sql or "/*" in sql:
        return False, "Commenti SQL non permessi"
    
    if sql.count(";") > 1:
        return False, "Query multiple non permesse"
    
    if " UNION " in sql_upper:
        return False, "UNION non permesso per sicurezza"
    
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    for word in forbidden:
        if f" {word} " in f" {sql_upper} " or sql_upper.startswith(f"{word} "):
            return False, f"Operazione {word} non permessa"
    
    if not validate_tables_in_sql(sql):
        return False, "Query contiene tabelle non permesse"
    
    return True, "OK"


def validate_sql_dynamic(sql: str) -> tuple[bool, str]:
    """
    Validate SQL for dynamic/custom databases (without table whitelist).
    
    This is used for user-uploaded databases where we can't know the table names
    in advance, but still need robust security validation.
    
    Args:
        sql: SQL query to validate
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not sql or not isinstance(sql, str):
        return False, "Empty or invalid SQL query"
    
    sql_clean = sql.strip()
    sql_upper = sql_clean.upper()
    
    # Must start with SELECT (case insensitive)
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed"
    
    # Block SQL comments (potential injection vector)
    if "--" in sql_clean:
        return False, "SQL comments (--) not allowed"
    if "/*" in sql_clean:
        return False, "SQL block comments not allowed"
    if "#" in sql_clean and not sql_clean.startswith("#"):  # MySQL comments
        # Allow # only at start (could be shebang in some contexts)
        return False, "SQL comments (#) not allowed"
    
    # Block multiple statements (semicolon injection)
    semicolon_count = sql_clean.count(";")
    if semicolon_count > 1:
        return False, "Multiple statements not allowed"
    # If there's one semicolon, it should only be at the end
    if semicolon_count == 1 and not sql_clean.rstrip().endswith(";"):
        return False, "Semicolon only allowed at end of query"
    
    # Block UNION (SQL injection to read other tables)
    if " UNION " in sql_upper or sql_upper.endswith(" UNION"):
        return False, "UNION not allowed for security"
    
    # Comprehensive list of forbidden operations
    # Using word boundary detection to avoid false positives
    import re
    forbidden_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", 
        "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE", 
        "COMMIT", "ROLLBACK", "SAVEPOINT",
        "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX",
        "LOAD_FILE", "INTO OUTFILE", "INTO DUMPFILE",  # MySQL file ops
        "COPY", "\\\\COPY",  # PostgreSQL file ops
        "XP_", "SP_",  # SQL Server system procs
        "UTL_", "DBMS_",  # Oracle packages
    ]
    
    for keyword in forbidden_keywords:
        # Match as whole word (word boundaries)
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Operation {keyword} not allowed"
    
    # Block hex/char encoding attacks
    if "0X" in sql_upper or "CHAR(" in sql_upper or "CHR(" in sql_upper:
        return False, "Encoded characters not allowed"
    
    # Block string concatenation tricks
    if "CONCAT(" in sql_upper and ("0X" in sql_upper or "CHAR" in sql_upper):
        return False, "String concatenation with encoding not allowed"
    
    # Block sleep/benchmark (timing attacks)
    if "SLEEP(" in sql_upper or "BENCHMARK(" in sql_upper or "WAITFOR" in sql_upper:
        return False, "Time-based functions not allowed"
    
    # Passed all checks
    return True, "OK"


def get_cache_stats() -> dict:
    """Restituisce statistiche sulla cache."""
    return {
        "size": len(sql_cache.cache),
        "max_size": sql_cache.max_size,
        "ttl_seconds": sql_cache.ttl.total_seconds()
    }


def clear_cache():
    """Svuota la cache SQL."""
    sql_cache.cache.clear()
    logger.info("Cache SQL svuotata")


# ============================================================================
# GENERAZIONE SQL PER DATABASE DINAMICI (UPLOAD UTENTE)
# ============================================================================

def fallback_generate_sql_dynamic(question: str, schema: str, tables: list) -> str:
    """
    Simple rule-based fallback SQL generator when AI is unavailable.
    Produces safe SELECT queries using heuristics for count/sum/avg/top/list.
    """
    q = (question or "").strip().lower()
    # Choose target table: try to find a table name in the question, else fallback to first table
    target_table = None
    for t in tables:
        if t.lower() in q or (t.lower().endswith('s') and t.lower()[:-1] in q) or (t.lower() + 's' in q):
            target_table = t
            break
    if not target_table and tables:
        target_table = tables[0]
    if not target_table:
        return "Error: No available tables in the database"

    # Heuristics
    if any(k in q for k in ("how many", "count of", "count", "how many records", "number of")):
        return f"SELECT COUNT(*) as count FROM {target_table};"

    if any(k in q for k in ("sum", "total", "totale", "revenue", "sales")):
        # Prefer 'total' or 'sales' if present in schema text
        column = None
        for cand in ("total", "sales", "amount", "revenue"):
            if cand in schema.lower():
                column = cand
                break
        if column:
            return f"SELECT SUM({column}) as total FROM {target_table};"
        else:
            return f"SELECT SUM(1) as total FROM {target_table};"  # fallback (will be 0 or invalid but still SELECT)

    if any(k in q for k in ("average", "avg", "media")):
        column = None
        for cand in ("total", "sales", "amount", "profit"):
            if cand in schema.lower():
                column = cand
                break
        if column:
            return f"SELECT AVG({column}) as average FROM {target_table};"
        else:
            return f"SELECT AVG(1) as average FROM {target_table};"

    # Top N
    import re
    m = re.search(r"top (\d+)", q)
    if m:
        n = int(m.group(1))
        # choose ordering column
        order_col = None
        for cand in ("profit", "total", "sales", "quantity"):
            if cand in schema.lower():
                order_col = cand
                break
        if order_col:
            return f"SELECT * FROM {target_table} ORDER BY {order_col} DESC LIMIT {n};"
        else:
            return f"SELECT * FROM {target_table} LIMIT {n};"

    # List/show -> return first 100 rows
    if any(k in q for k in ("show", "list", "display", "all", "mostra")):
        return f"SELECT * FROM {target_table} LIMIT 100;"

    # Default fallback
    return f"SELECT * FROM {target_table} LIMIT 100;"


def generate_sql_dynamic(question: str, schema: str, tables: list) -> str:
    """
    Genera una query SQL per database personalizzati caricati dall'utente.
    
    A differenza di generate_sql(), questa funzione:
    - Usa lo schema estratto dinamicamente dal database dell'utente
    - Non applica whitelist tabelle fissa
    - Adatta il prompt per schema sconosciuti
    
    Args:
        question: Domanda in linguaggio naturale
        schema: Schema del database in formato testuale
        tables: Lista delle tabelle disponibili
    
    Returns:
        Query SQL generata
    """
    if not question or not question.strip():
        return "Error: Domanda vuota"
    
    # Controlla cache
    cached_sql = sql_cache.get(question, schema)
    if cached_sql:
        return cached_sql
    
    # Controlla rate limiting
    if not rate_limiter.can_proceed():
        wait_time = rate_limiter.get_wait_time()
        return f"Error: Troppe richieste. Riprova tra {int(wait_time)} secondi."
    
    # If AI model is not available, use fallback rules
    if not model:
        logger.info("AI model not available - using fallback SQL generator")
        sql = fallback_generate_sql_dynamic(question, schema, tables)
        # cache and return if valid
        if sql and validate_sql(sql, check_tables=False):
            sql_cache.set(question, schema, sql)
            return sql
        return sql
    
    tables_list = ", ".join(tables)
    
    # Prompt ottimizzato per database dinamici
    prompt = f"""You are an expert SQL query generator. Generate a valid, safe SELECT SQL query based on the user's question.

STRICT RULES:
1. Generate ONLY SELECT queries - never INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE
2. Use ONLY tables and columns from the schema below
3. Use proper SQLite syntax
4. Return ONLY the SQL query, no explanations or markdown
5. Use table aliases for readability when appropriate
6. Always use explicit JOIN syntax when joining tables
7. If you're unsure about the exact column names, use the ones from the schema

AVAILABLE TABLES: {tables_list}

DATABASE SCHEMA:
{schema}

EXAMPLES:
- If asked "how many records" or "count", use: SELECT COUNT(*) as count FROM table_name;
- If asked "show all" or "list", use: SELECT * FROM table_name LIMIT 100;
- If asked about totals or sums, use: SELECT SUM(column) as total FROM table_name;
- If asked about averages, use: SELECT AVG(column) as average FROM table_name;
- For grouping data, use: SELECT column, COUNT(*) FROM table_name GROUP BY column;

NOW GENERATE SQL FOR:
Question: "{question}"
SQL:"""

    try:
        logger.info(f"Generazione SQL dinamico per: {question[:50]}...")
        response = model.generate_content(prompt)
        sql = response.text.strip()
        
        # Rimuovi markdown se presente
        if sql.startswith("```sql"):
            sql = sql[6:].strip()
        if sql.startswith("```"):
            sql = sql[3:].strip()
        if sql.endswith("```"):
            sql = sql[:-3].strip()
        
        # Rimuovi newline multipli
        sql = " ".join(sql.split())
        
        # Validazione base (no check tabelle)
        if validate_sql(sql, check_tables=False):
            sql_cache.set(question, schema, sql)
        
        logger.info(f"SQL dinamico generato: {sql[:80]}...")
        return sql
        
    except Exception as e:
        logger.error(f"Errore generazione SQL dinamico: {str(e)}")
        return f"Error: {str(e)}"