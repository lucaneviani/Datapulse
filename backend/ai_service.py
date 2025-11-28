"""
DataPulse AI Service
=====================
Servizio per generazione SQL tramite AI con caching e rate limiting.
"""

import google.generativeai as genai
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
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
else:
    model = None
    logger.warning("GOOGLE_API_KEY non configurata - AI service disabilitato")

# ============================================================================
# CACHE PER QUERY SQL
# ============================================================================

class SQLCache:
    """Cache in memoria per query SQL generate."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[str, datetime]] = {}
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def _hash_key(self, question: str, schema: str) -> str:
        """Genera una chiave hash per la cache."""
        content = f"{question.lower().strip()}:{schema}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, question: str, schema: str) -> Optional[str]:
        """Recupera SQL dalla cache se presente e non scaduto."""
        key = self._hash_key(question, schema)
        if key in self.cache:
            sql, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                logger.info(f"Cache HIT per: {question[:30]}...")
                return sql
            else:
                # Rimuovi entry scaduta
                del self.cache[key]
        return None
    
    def set(self, question: str, schema: str, sql: str):
        """Salva SQL nella cache."""
        # Pulisci cache se piena
        if len(self.cache) >= self.max_size:
            self._cleanup()
        
        key = self._hash_key(question, schema)
        self.cache[key] = (sql, datetime.now())
        logger.info(f"Cache SET per: {question[:30]}...")
    
    def _cleanup(self):
        """Rimuove le entry più vecchie."""
        now = datetime.now()
        # Rimuovi scadute
        expired = [k for k, (_, ts) in self.cache.items() if now - ts >= self.ttl]
        for k in expired:
            del self.cache[k]
        
        # Se ancora piena, rimuovi le più vecchie
        if len(self.cache) >= self.max_size:
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            for k, _ in sorted_items[:len(self.cache) // 2]:
                del self.cache[k]


# Istanza globale della cache
sql_cache = SQLCache(max_size=100, ttl_seconds=3600)  # 1 ora TTL

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Rate limiter semplice per proteggere l'API."""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: list = []
    
    def can_proceed(self) -> bool:
        """Verifica se possiamo procedere con una nuova richiesta."""
        now = time.time()
        # Rimuovi richieste vecchie
        self.requests = [ts for ts in self.requests if now - ts < self.window]
        
        if len(self.requests) >= self.max_requests:
            logger.warning(f"Rate limit raggiunto: {len(self.requests)}/{self.max_requests}")
            return False
        
        self.requests.append(now)
        return True
    
    def get_wait_time(self) -> float:
        """Calcola tempo di attesa se rate limited."""
        if not self.requests:
            return 0
        return max(0, self.window - (time.time() - self.requests[0]))


# Istanza globale del rate limiter
rate_limiter = RateLimiter(max_requests=30, window_seconds=60)

# ============================================================================
# WHITELIST TABELLE E COLONNE (SICUREZZA)
# ============================================================================

# Tabelle permesse nel database
ALLOWED_TABLES = {
    "customers", "products", "orders", "order_items"
}

# Colonne permesse per tabella
ALLOWED_COLUMNS = {
    "customers": {"id", "name", "segment", "country", "city", "state", "postal_code", "region"},
    "products": {"id", "name", "category", "sub_category"},
    "orders": {"id", "customer_id", "order_date", "ship_date", "ship_mode", "total"},
    "order_items": {"id", "order_id", "product_id", "quantity", "sales", "discount", "profit"}
}

# Alias comuni per tabelle
TABLE_ALIASES = {
    "c": "customers",
    "p": "products", 
    "o": "orders",
    "oi": "order_items"
}

# ============================================================================
# SANITIZZAZIONE INPUT
# ============================================================================

def sanitize_input(text: str) -> str:
    """
    Sanitizza l'input dell'utente rimuovendo caratteri potenzialmente pericolosi.
    
    Args:
        text: Testo da sanitizzare
    
    Returns:
        Testo sanitizzato
    """
    if not text:
        return ""
    
    # Rimuovi caratteri di controllo
    import re
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Rimuovi tag HTML/script
    text = re.sub(r'<[^>]*>', '', text)
    
    # Limita caratteri speciali SQL pericolosi all'inizio/fine
    text = text.strip(";'\"")
    
    return text.strip()


def validate_tables_in_sql(sql: str) -> bool:
    """
    Verifica che la query SQL usi solo tabelle permesse.
    
    Args:
        sql: Query SQL da verificare
    
    Returns:
        True se tutte le tabelle sono permesse, False altrimenti
    """
    import re
    sql_upper = sql.upper()
    
    # Pattern per trovare nomi tabelle dopo FROM e JOIN
    # Cattura: FROM table, JOIN table, FROM table alias
    table_pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(table_pattern, sql_upper)
    
    for table in matches:
        table_lower = table.lower()
        # Verifica se è una tabella o un alias permesso
        if table_lower not in ALLOWED_TABLES and table_lower not in TABLE_ALIASES:
            logger.warning(f"Tabella non permessa rilevata: {table}")
            return False
    
    return True


# ============================================================================
# SCHEMA DESCRITTIVO PER AI
# ============================================================================

ENHANCED_SCHEMA = """
Table: customers
- id: INTEGER PRIMARY KEY (identificatore univoco cliente)
- name: TEXT (nome completo del cliente)
- segment: TEXT (segmento mercato: 'Consumer', 'Corporate', 'Home Office')
- country: TEXT (paese del cliente)
- city: TEXT (città del cliente)
- state: TEXT (stato/regione del cliente)
- postal_code: TEXT (codice postale)
- region: TEXT (macro-regione: 'West', 'East', 'Central', 'South')

Table: products
- id: INTEGER PRIMARY KEY (identificatore univoco prodotto)
- name: TEXT (nome del prodotto)
- category: TEXT (categoria: 'Technology', 'Furniture', 'Office Supplies')
- sub_category: TEXT (sotto-categoria del prodotto)

Table: orders
- id: INTEGER PRIMARY KEY (identificatore univoco ordine)
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