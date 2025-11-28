"""
Unit Tests per AI Service - DataPulse
=====================================
Testa la generazione SQL e la validazione di sicurezza.
"""

import pytest
import sys
import os

# Aggiungi il path del progetto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_service import validate_sql, SQLCache, RateLimiter, get_cache_stats, clear_cache


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
