"""
DataPulse Database Manager Tests

Unit tests for session management and security features.
Tests for A2 (Race Condition), A3 (Path Traversal) fixes.
"""

import pytest
import sys
import os
import threading
import time

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database_manager import SessionManager, session_manager, get_session_tables, execute_query_on_session


class TestSessionManagerBasic:
    """Test base per SessionManager."""
    
    def test_create_session(self):
        """Creazione sessione deve funzionare."""
        manager = SessionManager()
        session_id = manager.create_session()
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        
    def test_get_session(self):
        """Recupero sessione deve funzionare."""
        manager = SessionManager()
        session_id = manager.create_session()
        
        session = manager.get_session(session_id)
        
        assert session is not None
        assert session["id"] == session_id
        assert session["db_type"] == "demo"
        
    def test_get_invalid_session(self):
        """Sessione inesistente deve restituire None."""
        manager = SessionManager()
        session = manager.get_session("non-existent-session-id")
        
        assert session is None
        
    def test_delete_session(self):
        """Eliminazione sessione deve funzionare."""
        manager = SessionManager()
        session_id = manager.create_session()
        
        manager.delete_session(session_id)
        session = manager.get_session(session_id)
        
        assert session is None


class TestSessionIdValidation:
    """Test per validazione session_id (A3 fix - Path Traversal)."""
    
    def test_valid_uuid4_accepted(self):
        """UUID4 valido deve essere accettato."""
        manager = SessionManager()
        
        # Valid UUID4 format
        valid_ids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-41d1-80b4-00c04fd430c8",
            "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        ]
        
        for sid in valid_ids:
            assert manager._is_valid_session_id(sid) == True
    
    def test_invalid_uuid_rejected(self):
        """UUID non valido deve essere rifiutato."""
        manager = SessionManager()
        
        invalid_ids = [
            "",
            None,
            "not-a-uuid",
            "12345",
            "../../../etc/passwd",
            "550e8400-e29b-41d4-a716",  # Incomplete
            "550e8400e29b41d4a716446655440000",  # No dashes
        ]
        
        for sid in invalid_ids:
            assert manager._is_valid_session_id(sid) == False
    
    def test_path_traversal_blocked(self):
        """Tentativi di path traversal devono essere bloccati."""
        manager = SessionManager()
        
        malicious_ids = [
            "../secret",
            "..\\..\\windows\\system32",
            "uploads/../../../etc/passwd",
            "valid-uuid/../../../secrets",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]
        
        for sid in malicious_ids:
            assert manager._is_valid_session_id(sid) == False


class TestSecureFilename:
    """Test per sanitizzazione filename (A3 fix)."""
    
    def test_normal_filename(self):
        """Filename normale deve essere preservato."""
        manager = SessionManager()
        
        assert manager._secure_filename("data.csv") == "data.csv"
        assert manager._secure_filename("my_file.xlsx") == "my_file.xlsx"
    
    def test_path_traversal_removed(self):
        """Path traversal deve essere rimosso."""
        manager = SessionManager()
        
        result = manager._secure_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result
    
    def test_null_bytes_removed(self):
        """Null bytes devono essere rimossi."""
        manager = SessionManager()
        
        result = manager._secure_filename("file\x00.csv")
        assert "\x00" not in result
    
    def test_dangerous_chars_replaced(self):
        """Caratteri pericolosi devono essere sostituiti."""
        manager = SessionManager()
        
        result = manager._secure_filename("file<>:|?.csv")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "|" not in result
        assert "?" not in result
    
    def test_empty_filename(self):
        """Filename vuoto deve restituire default."""
        manager = SessionManager()
        
        result = manager._secure_filename("")
        assert result == "unnamed"
        
        result = manager._secure_filename(None)
        assert result == "unnamed"
    
    def test_filename_length_limited(self):
        """Filename troppo lungo deve essere troncato."""
        manager = SessionManager()
        
        long_name = "a" * 200 + ".csv"
        result = manager._secure_filename(long_name)
        assert len(result) <= 100


class TestThreadSafety:
    """Test per thread safety (A2 fix - Race Condition)."""
    
    def test_concurrent_session_creation(self):
        """Creazione concorrente sessioni deve essere thread-safe."""
        manager = SessionManager()
        session_ids = []
        errors = []
        
        def create_session():
            try:
                sid = manager.create_session()
                session_ids.append(sid)
            except Exception as e:
                errors.append(str(e))
        
        # Create 20 sessions concurrently
        threads = [threading.Thread(target=create_session) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should succeed without errors
        assert len(errors) == 0
        assert len(session_ids) == 20
        # All session IDs should be unique
        assert len(set(session_ids)) == 20
    
    def test_concurrent_session_access(self):
        """Accesso concorrente a sessione deve essere thread-safe."""
        manager = SessionManager()
        session_id = manager.create_session()
        results = []
        errors = []
        
        def access_session():
            try:
                for _ in range(10):
                    session = manager.get_session(session_id)
                    if session:
                        results.append(session["id"])
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(str(e))
        
        # 10 threads accessing same session
        threads = [threading.Thread(target=access_session) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(results) == 100  # 10 threads x 10 accesses
    
    def test_concurrent_create_and_delete(self):
        """Creazione e cancellazione concorrente deve essere thread-safe."""
        manager = SessionManager()
        errors = []
        
        def create_and_delete():
            try:
                for _ in range(5):
                    sid = manager.create_session()
                    manager.get_session(sid)
                    manager.delete_session(sid)
            except Exception as e:
                errors.append(str(e))
        
        threads = [threading.Thread(target=create_and_delete) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestResetToDemo:
    """Test per reset_to_demo con validazione."""
    
    def test_reset_valid_session(self):
        """Reset sessione valida deve funzionare."""
        manager = SessionManager()
        session_id = manager.create_session()
        
        success, message = manager.reset_to_demo(session_id)
        
        assert success == True
        assert "reset" in message.lower() or "demo" in message.lower()
    
    def test_reset_invalid_session_id_format(self):
        """Reset con session_id non valido deve fallire."""
        manager = SessionManager()
        
        success, message = manager.reset_to_demo("../../../etc/passwd")
        
        assert success == False
        assert "Invalid" in message
    
    def test_reset_nonexistent_session(self):
        """Reset sessione inesistente deve fallire."""
        manager = SessionManager()
        
        success, message = manager.reset_to_demo("550e8400-e29b-41d4-a716-446655440000")
        
        assert success == False


class TestUploadCSV:
    """Test per l'upload di file CSV/Excel e la creazione del DB sessione."""

    def test_upload_csv_creates_table(self):
        # Use the module-level singleton to ensure module helpers see the session
        session_id = session_manager.create_session()

        csv_content = b"col1,col2\n1,foo\n2,bar\n"
        success, message = session_manager.upload_csv(session_id, [("data.csv", csv_content)])
        assert success is True, f"Upload failed: {message}"

        ok, tables = get_session_tables(session_id)
        assert ok is True
        assert len(tables) >= 1
        created_table = tables[0]
        assert created_table.startswith("data") or "data" in created_table

        ok, res = execute_query_on_session(session_id, f"SELECT * FROM {created_table} LIMIT 2")
        assert ok is True
        assert len(res) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
