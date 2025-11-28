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

from backend.ai_service import validate_sql


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
