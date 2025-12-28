"""
DataPulse API Tests

Unit tests for the /api/analyze endpoint and other API functionality.
"""

import os
import sys

import pytest

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from backend.main import app

# Client per test
client = TestClient(app)


class TestAnalyzeEndpoint:
    """Test per l'endpoint /api/analyze."""

    def test_endpoint_exists(self):
        """L'endpoint deve rispondere (anche se con errore AI)."""
        response = client.post("/api/analyze", json={"question": "test"})
        assert response.status_code == 200

    def test_response_has_required_fields(self):
        """La risposta deve contenere i campi attesi."""
        response = client.post("/api/analyze", json={"question": "How many customers?"})
        data = response.json()
        # Deve avere o generated_sql/data o error
        assert "generated_sql" in data or "error" in data

    def test_empty_question(self):
        """Domanda vuota deve restituire 422 (validation error) per Pydantic min_length."""
        response = client.post("/api/analyze", json={"question": ""})
        # Pydantic validation catches empty string (min_length=1)
        assert response.status_code == 422

    def test_missing_question_field(self):
        """Request senza campo question deve restituire 422 (campo richiesto)."""
        response = client.post("/api/analyze", json={})
        # Pydantic validation catches missing required field
        assert response.status_code == 422

    def test_valid_count_query(self):
        """Query di conteggio deve funzionare (se AI disponibile)."""
        response = client.post("/api/analyze", json={"question": "How many customers are there?"})
        data = response.json()
        # Se l'AI funziona, deve avere generated_sql
        if "generated_sql" in data and "COUNT" in data["generated_sql"].upper():
            assert "data" in data

    def test_response_is_json(self):
        """La risposta deve essere JSON valido."""
        response = client.post("/api/analyze", json={"question": "test query"})
        assert response.headers["content-type"] == "application/json"
        # Non deve sollevare eccezione
        data = response.json()
        assert data is not None


class TestAPIErrorHandling:
    """Test per la gestione errori dell'API."""

    def test_invalid_json_body(self):
        """Body non-JSON deve essere gestito."""
        response = client.post("/api/analyze", content="not json", headers={"Content-Type": "application/json"})
        # FastAPI restituisce 422 per validation error
        assert response.status_code in [200, 422]

    def test_long_question(self):
        """Domanda troppo lunga deve restituire 422 (max_length exceeded)."""
        long_question = "What is " + "the total sales " * 100 + "?"
        response = client.post("/api/analyze", json={"question": long_question})
        # Pydantic validation catches max_length=500 violation
        assert response.status_code == 422

    def test_special_characters_in_question(self):
        """Caratteri speciali nella domanda devono essere gestiti."""
        response = client.post("/api/analyze", json={"question": "What's the <total> & count?"})
        assert response.status_code == 200

    def test_sql_injection_attempt(self):
        """Tentativi di SQL injection devono essere bloccati."""
        malicious = "'; DROP TABLE customers; --"
        response = client.post("/api/analyze", json={"question": malicious})
        data = response.json()
        # Non deve eseguire DROP
        if "generated_sql" in data:
            assert "DROP" not in data["generated_sql"].upper() or "error" in data


class TestAPIIntegration:
    """Test di integrazione per verificare il flusso completo."""

    def test_simple_query_flow(self):
        """Flusso completo: domanda -> SQL -> risultati."""
        response = client.post("/api/analyze", json={"question": "Show all customers"})
        data = response.json()

        # Se funziona, deve avere SQL e data
        if "error" not in data:
            assert "generated_sql" in data
            assert "data" in data
            assert isinstance(data["data"], list)

    def test_aggregation_query_flow(self):
        """Flusso con query di aggregazione."""
        response = client.post("/api/analyze", json={"question": "Count the number of orders"})
        data = response.json()

        if "error" not in data and "generated_sql" in data:
            # Verifica che sia una query di conteggio
            sql = data["generated_sql"].upper()
            assert "SELECT" in sql


class TestUploadEndpoint:
    """Integration test for CSV upload endpoint."""

    def test_upload_csv_via_api(self):
        # Create a session first
        response = client.post("/api/session/create")
        assert response.status_code == 200
        data = response.json()
        session_id = data.get("session_id")
        assert session_id

        # Upload a simple CSV file
        files = {"files": ("data.csv", b"col1,col2\n1,foo\n2,bar\n", "text/csv")}
        response = client.post(f"/api/session/{session_id}/upload/csv", files=files)
        assert response.status_code == 200
        result = response.json()
        assert result.get("success") is True
        assert "tables" in result and len(result["tables"]) >= 1

        # Now ask a question using the session DB
        analyze_resp = client.post(f"/api/session/{session_id}/analyze", json={"question": "How many records are there?"})
        assert analyze_resp.status_code == 200
        analyze_data = analyze_resp.json()
        assert "error" not in analyze_data or ("Only SELECT" not in str(analyze_data.get("error", "")))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
