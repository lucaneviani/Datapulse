"""
DataPulse AI Service Tests

Unit tests for SQL generation and security validation.
"""

import pytest
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_service import (
    validate_sql, validate_sql_strict, validate_tables_in_sql,
    sanitize_input, SQLCache, RateLimiter, get_cache_stats, clear_cache,
    ALLOWED_TABLES, ALLOWED_COLUMNS
)


class TestValidateSQL:
    """Test per la funzione validate_sql."""
    
    def test_valid_select_query(self):
        """SELECT semplice deve essere valido."""
        assert validate_sql("SELECT * FROM customers") == True
        
    def test_valid_select_with_where(self):
        """SELECT con WHERE deve essere valido."""
        assert validate_sql("SELECT name FROM customers WHERE id = 1") == True
        
    def test_valid_select_with_join(self):
        """SELECT con JOIN deve essere valido."""
        sql = "SELECT c.name, o.total FROM customers c JOIN orders o ON c.id = o.customer_id"
        assert validate_sql(sql) == True
        
    def test_valid_select_with_aggregation(self):
        """SELECT con aggregazioni deve essere valido."""
        assert validate_sql("SELECT COUNT(*) FROM customers") == True
        assert validate_sql("SELECT SUM(total) FROM orders") == True
        assert validate_sql("SELECT region, AVG(total) FROM orders GROUP BY region") == True
        
    def test_invalid_insert_query(self):
        """INSERT deve essere rifiutato."""
        assert validate_sql("INSERT INTO customers VALUES (1, 'Test')") == False
        
    def test_invalid_update_query(self):
        """UPDATE deve essere rifiutato."""
        assert validate_sql("UPDATE customers SET name = 'Test' WHERE id = 1") == False
        
    def test_invalid_delete_query(self):
        """DELETE deve essere rifiutato."""
        assert validate_sql("DELETE FROM customers WHERE id = 1") == False
        
    def test_invalid_drop_query(self):
        """DROP deve essere rifiutato."""
        assert validate_sql("DROP TABLE customers") == False
        
    def test_invalid_alter_query(self):
        """ALTER deve essere rifiutato."""
        assert validate_sql("ALTER TABLE customers ADD COLUMN age INT") == False
        
    def test_invalid_create_query(self):
        """CREATE deve essere rifiutato."""
        assert validate_sql("CREATE TABLE test (id INT)") == False
        
    def test_invalid_truncate_query(self):
        """TRUNCATE deve essere rifiutato."""
        assert validate_sql("TRUNCATE TABLE customers") == False
        
    def test_empty_query(self):
        """Query vuota deve essere rifiutata."""
        assert validate_sql("") == False
        assert validate_sql(None) == False
        
    def test_non_string_query(self):
        """Input non-stringa deve essere rifiutato."""
        assert validate_sql(123) == False
        assert validate_sql([]) == False
        assert validate_sql({}) == False
        
    def test_case_insensitive_detection(self):
        """La validazione deve essere case-insensitive per parole chiave pericolose."""
        assert validate_sql("select * from customers") == True  # lowercase SELECT ok
        assert validate_sql("insert into customers values (1)") == False  # lowercase INSERT blocked
        assert validate_sql("Select * From Customers") == True  # mixed case SELECT ok
        
    def test_injection_attempts(self):
        """Tentativi di SQL injection devono essere bloccati."""
        # SELECT con DELETE nascosto
        assert validate_sql("SELECT * FROM customers; DELETE FROM customers") == False
        # SELECT con DROP nascosto
        assert validate_sql("SELECT * FROM customers; DROP TABLE customers") == False
        
    def test_subquery_valid(self):
        """Subquery SELECT deve essere valida."""
        sql = "SELECT * FROM customers WHERE id IN (SELECT customer_id FROM orders)"
        assert validate_sql(sql) == True
    
    def test_sql_comments_blocked(self):
        """Commenti SQL devono essere bloccati (possibile injection)."""
        assert validate_sql("SELECT * FROM customers -- malicious") == False
        assert validate_sql("SELECT * FROM customers /* comment */") == False


class TestValidateSQLEdgeCases:
    """Test per edge cases della validazione SQL."""
    
    def test_whitespace_handling(self):
        """Query con spazi extra deve essere gestita correttamente."""
        assert validate_sql("  SELECT * FROM customers  ") == True
        assert validate_sql("\nSELECT * FROM customers\n") == True
        
    def test_multiline_query(self):
        """Query multilinea deve essere valida."""
        sql = """
        SELECT 
            c.name,
            COUNT(o.id) as order_count
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        GROUP BY c.name
        """
        assert validate_sql(sql) == True
        
    def test_error_message_not_valid(self):
        """Messaggi di errore dall'AI non devono essere validi."""
        assert validate_sql("Error: API key not found") == False
        assert validate_sql("I cannot generate SQL for this question") == False


class TestSQLCache:
    """Test per il sistema di caching SQL."""
    
    def test_cache_set_and_get(self):
        """Cache deve salvare e recuperare query."""
        cache = SQLCache(max_size=10, ttl_seconds=3600)
        cache.set("How many customers?", "schema", "SELECT COUNT(*) FROM customers")
        result = cache.get("How many customers?", "schema")
        assert result == "SELECT COUNT(*) FROM customers"
    
    def test_cache_miss(self):
        """Cache miss deve restituire None."""
        cache = SQLCache(max_size=10, ttl_seconds=3600)
        result = cache.get("Unknown question", "schema")
        assert result is None
    
    def test_cache_case_insensitive(self):
        """Cache deve essere case-insensitive per le domande."""
        cache = SQLCache(max_size=10, ttl_seconds=3600)
        cache.set("How Many Customers?", "schema", "SELECT COUNT(*) FROM customers")
        result = cache.get("how many customers?", "schema")
        assert result == "SELECT COUNT(*) FROM customers"
    
    def test_cache_max_size(self):
        """Cache deve rispettare la dimensione massima."""
        cache = SQLCache(max_size=3, ttl_seconds=3600)
        for i in range(5):
            cache.set(f"Question {i}", "schema", f"SQL {i}")
        assert len(cache.cache) <= 3


class TestRateLimiter:
    """Test per il rate limiter."""
    
    def test_rate_limiter_allows_requests(self):
        """Rate limiter deve permettere richieste sotto il limite."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.can_proceed() == True
    
    def test_rate_limiter_blocks_excess(self):
        """Rate limiter deve bloccare richieste oltre il limite."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.can_proceed()
        assert limiter.can_proceed() == False
    
    def test_rate_limiter_wait_time(self):
        """Rate limiter deve calcolare tempo di attesa."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.can_proceed()
        wait_time = limiter.get_wait_time()
        assert wait_time > 0 and wait_time <= 60


class TestCacheStats:
    """Test per statistiche cache."""
    
    def test_get_cache_stats(self):
        """get_cache_stats deve restituire dati validi."""
        stats = get_cache_stats()
        assert "size" in stats
        assert "max_size" in stats
        assert "ttl_seconds" in stats
    
    def test_clear_cache(self):
        """clear_cache deve svuotare la cache."""
        # Questo test verifica che la funzione non sollevi eccezioni
        clear_cache()
        stats = get_cache_stats()
        assert stats["size"] == 0


class TestSanitizeInput:
    """Test per la sanitizzazione input."""
    
    def test_sanitize_removes_html(self):
        """Sanitize deve rimuovere tag HTML."""
        result = sanitize_input("<script>alert('xss')</script>Question")
        assert "<script>" not in result
        assert "Question" in result
    
    def test_sanitize_removes_control_chars(self):
        """Sanitize deve rimuovere caratteri di controllo."""
        result = sanitize_input("Hello\x00World")
        assert "\x00" not in result
    
    def test_sanitize_strips_sql_chars(self):
        """Sanitize deve rimuovere caratteri SQL pericolosi all'inizio/fine."""
        result = sanitize_input(";'SELECT * FROM users\"")
        assert not result.startswith(";")
        assert not result.endswith("\"")
    
    def test_sanitize_preserves_normal_text(self):
        """Sanitize deve preservare testo normale."""
        result = sanitize_input("How many customers are there?")
        assert result == "How many customers are there?"
    
    def test_sanitize_empty_input(self):
        """Sanitize deve gestire input vuoto."""
        assert sanitize_input("") == ""
        assert sanitize_input(None) == ""


class TestTableWhitelist:
    """Test per la whitelist delle tabelle."""
    
    def test_allowed_tables_exist(self):
        """Verifica che le tabelle permesse siano definite."""
        assert "customers" in ALLOWED_TABLES
        assert "products" in ALLOWED_TABLES
        assert "orders" in ALLOWED_TABLES
        assert "order_items" in ALLOWED_TABLES
    
    def test_validate_tables_allowed(self):
        """Query con tabelle permesse deve essere valida."""
        sql = "SELECT * FROM customers"
        assert validate_tables_in_sql(sql) == True
        
        sql = "SELECT * FROM customers c JOIN orders o ON c.id = o.customer_id"
        assert validate_tables_in_sql(sql) == True
    
    def test_validate_tables_not_allowed(self):
        """Query con tabelle non permesse deve essere rifiutata."""
        sql = "SELECT * FROM users"
        assert validate_tables_in_sql(sql) == False
        
        sql = "SELECT * FROM customers JOIN hackers ON 1=1"
        assert validate_tables_in_sql(sql) == False
    
    def test_validate_tables_with_aliases(self):
        """Query con alias di tabella deve essere valida."""
        sql = "SELECT c.name FROM customers c"
        assert validate_tables_in_sql(sql) == True


class TestValidateSQLStrict:
    """Test per la validazione SQL strict con messaggi."""
    
    def test_strict_valid_query(self):
        """Query valida deve passare con messaggio OK."""
        is_valid, msg = validate_sql_strict("SELECT * FROM customers")
        assert is_valid == True
        assert msg == "OK"
    
    def test_strict_empty_query(self):
        """Query vuota deve fallire con messaggio appropriato."""
        is_valid, msg = validate_sql_strict("")
        assert is_valid == False
        assert "vuota" in msg.lower() or "non valida" in msg.lower()
    
    def test_strict_non_select(self):
        """Query non-SELECT deve fallire con messaggio appropriato."""
        is_valid, msg = validate_sql_strict("INSERT INTO customers VALUES (1)")
        assert is_valid == False
        assert "SELECT" in msg
    
    def test_strict_union_blocked(self):
        """UNION deve essere bloccato con messaggio."""
        is_valid, msg = validate_sql_strict("SELECT * FROM customers UNION SELECT * FROM products")
        assert is_valid == False
        assert "UNION" in msg
    
    def test_strict_forbidden_tables(self):
        """Tabelle non permesse devono essere bloccate."""
        is_valid, msg = validate_sql_strict("SELECT * FROM secret_data")
        assert is_valid == False
        assert "tabelle" in msg.lower()


class TestUnionBlocking:
    """Test per il blocco di UNION (sicurezza aggiuntiva Fase 3)."""
    
    def test_union_blocked(self):
        """UNION deve essere bloccato."""
        sql = "SELECT * FROM customers UNION SELECT * FROM products"
        assert validate_sql(sql, check_tables=False) == False
    
    def test_union_all_blocked(self):
        """UNION ALL deve essere bloccato."""
        sql = "SELECT * FROM customers UNION ALL SELECT * FROM products"
        assert validate_sql(sql, check_tables=False) == False


class TestValidateSQLDynamic:
    """Test per validate_sql_dynamic - validazione per database dinamici (A1 fix)."""
    
    def test_valid_select_query(self):
        """Query SELECT valida deve passare."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT * FROM any_table")
        assert is_valid == True
        assert msg == "OK"
    
    def test_valid_complex_query(self):
        """Query SELECT complessa deve passare."""
        from backend.ai_service import validate_sql_dynamic
        sql = "SELECT a.col1, SUM(b.col2) FROM table_a a JOIN table_b b ON a.id = b.id GROUP BY a.col1"
        is_valid, msg = validate_sql_dynamic(sql)
        assert is_valid == True
    
    def test_empty_query_rejected(self):
        """Query vuota deve essere rifiutata."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("")
        assert is_valid == False
        assert "Empty" in msg or "invalid" in msg
    
    def test_non_select_rejected(self):
        """Query non-SELECT deve essere rifiutata."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("INSERT INTO table VALUES (1)")
        assert is_valid == False
        assert "SELECT" in msg
    
    def test_drop_blocked(self):
        """DROP deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT 1; DROP TABLE users")
        assert is_valid == False
    
    def test_delete_blocked(self):
        """DELETE deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("DELETE FROM users WHERE 1=1")
        assert is_valid == False
    
    def test_update_blocked(self):
        """UPDATE deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("UPDATE users SET admin=1")
        assert is_valid == False
    
    def test_insert_blocked(self):
        """INSERT deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("INSERT INTO users VALUES ('hacker')")
        assert is_valid == False
    
    def test_sql_comments_blocked(self):
        """Commenti SQL devono essere bloccati."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT * FROM users -- comment")
        assert is_valid == False
        assert "comment" in msg.lower()
        
        is_valid, msg = validate_sql_dynamic("SELECT * FROM users /* block */")
        assert is_valid == False
    
    def test_union_blocked(self):
        """UNION deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT a FROM t1 UNION SELECT b FROM t2")
        assert is_valid == False
        assert "UNION" in msg
    
    def test_multiple_statements_blocked(self):
        """Statement multipli devono essere bloccati."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT 1; SELECT 2")
        assert is_valid == False
        assert "Multiple" in msg or "semicolon" in msg.lower() or "statements" in msg.lower()
    
    def test_semicolon_at_end_allowed(self):
        """Punto e virgola alla fine deve essere permesso."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT * FROM users;")
        assert is_valid == True
    
    def test_semicolon_in_middle_blocked(self):
        """Punto e virgola a metà query deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT 1; DROP TABLE users")
        assert is_valid == False
    
    def test_exec_blocked(self):
        """EXEC/EXECUTE devono essere bloccati."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("EXEC sp_executesql")
        assert is_valid == False
    
    def test_pragma_blocked(self):
        """PRAGMA deve essere bloccato (SQLite)."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("PRAGMA table_info(users)")
        assert is_valid == False
    
    def test_attach_blocked(self):
        """ATTACH deve essere bloccato (SQLite)."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("ATTACH DATABASE '/etc/passwd' AS pwd")
        assert is_valid == False
    
    def test_sleep_blocked(self):
        """SLEEP (timing attack) deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT SLEEP(10)")
        assert is_valid == False
        assert "Time" in msg or "function" in msg.lower()
    
    def test_benchmark_blocked(self):
        """BENCHMARK (timing attack) deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT BENCHMARK(1000000, SHA1('test'))")
        assert is_valid == False
    
    def test_hex_encoding_blocked(self):
        """Codifica hex deve essere bloccata."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT 0x44524F50205441424C45")
        assert is_valid == False
        assert "Encoded" in msg or "character" in msg.lower()
    
    def test_char_encoding_blocked(self):
        """CHAR() encoding deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT CHAR(68,82,79,80)")
        assert is_valid == False
    
    def test_load_file_blocked(self):
        """LOAD_FILE deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT LOAD_FILE('/etc/passwd')")
        assert is_valid == False
    
    def test_into_outfile_blocked(self):
        """INTO OUTFILE deve essere bloccato."""
        from backend.ai_service import validate_sql_dynamic
        is_valid, msg = validate_sql_dynamic("SELECT * FROM users INTO OUTFILE '/tmp/data'")
        assert is_valid == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
