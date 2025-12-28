"""
Tests for DataPulse Pydantic Schemas

B3: Centralized Pydantic Schemas - Test Coverage

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import pytest
from pydantic import ValidationError

from backend.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AuthResponse,
    ChartType,
    DashboardCreateRequest,
    ErrorResponse,
    ExportFormat,
    ExportRequest,
    HealthCheckResponse,
    LoginRequest,
    RegisterRequest,
    SavedQuery,
    SchemaResponse,
    SessionCreateResponse,
)


class TestAnalyzeRequest:
    """Tests for AnalyzeRequest schema."""

    def test_valid_question(self):
        """Valid questions should be accepted."""
        req = AnalyzeRequest(question="How many customers are there?")
        assert req.question == "How many customers are there?"

    def test_question_stripped(self):
        """Whitespace should be stripped from questions."""
        req = AnalyzeRequest(question="  test question  ")
        assert req.question == "test question"

    def test_empty_question_rejected(self):
        """Empty questions should be rejected."""
        with pytest.raises(ValidationError) as exc:
            AnalyzeRequest(question="")
        # Pydantic uses 'string_too_short' type for min_length violations
        error_str = str(exc.value).lower()
        assert "string_too_short" in error_str or "min_length" in error_str or "character" in error_str

    def test_whitespace_only_rejected(self):
        """Whitespace-only questions should be rejected."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(question="   ")

    def test_long_question_rejected(self):
        """Questions over 500 characters should be rejected."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(question="x" * 501)

    def test_xss_script_tag_rejected(self):
        """XSS script tags should be rejected."""
        with pytest.raises(ValidationError) as exc:
            AnalyzeRequest(question="<script>alert('xss')</script>")
        assert "invalid" in str(exc.value).lower()

    def test_xss_javascript_rejected(self):
        """JavaScript URIs should be rejected."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(question="javascript:alert(1)")


class TestAnalyzeResponse:
    """Tests for AnalyzeResponse schema."""

    def test_valid_response(self):
        """Valid response should be accepted."""
        resp = AnalyzeResponse(generated_sql="SELECT COUNT(*) FROM customers", data=[{"count": 100}], row_count=1)
        assert resp.row_count == 1
        assert len(resp.data) == 1

    def test_empty_data_allowed(self):
        """Empty data list should be allowed."""
        resp = AnalyzeResponse(generated_sql="SELECT * FROM empty_table", data=[], row_count=0)
        assert resp.row_count == 0

    def test_negative_row_count_rejected(self):
        """Negative row counts should be rejected."""
        with pytest.raises(ValidationError):
            AnalyzeResponse(generated_sql="SELECT 1", data=[], row_count=-1)


class TestRegisterRequest:
    """Tests for RegisterRequest schema."""

    def test_valid_registration(self):
        """Valid registration should be accepted."""
        req = RegisterRequest(username="testuser", email="test@example.com", password="TestPass123")
        assert req.username == "testuser"
        assert req.email == "test@example.com"

    def test_username_too_short(self):
        """Username under 3 characters should be rejected."""
        with pytest.raises(ValidationError):
            RegisterRequest(username="ab", email="test@example.com", password="TestPass123")

    def test_invalid_username_chars(self):
        """Username with invalid characters should be rejected."""
        with pytest.raises(ValidationError):
            RegisterRequest(username="user@name", email="test@example.com", password="TestPass123")

    def test_invalid_email_format(self):
        """Invalid email format should be rejected."""
        with pytest.raises(ValidationError):
            RegisterRequest(username="testuser", email="notanemail", password="TestPass123")

    def test_email_normalized_lowercase(self):
        """Email should be normalized to lowercase."""
        req = RegisterRequest(username="testuser", email="Test@Example.COM", password="TestPass123")
        assert req.email == "test@example.com"

    def test_password_too_short(self):
        """Password under 8 characters should be rejected."""
        with pytest.raises(ValidationError):
            RegisterRequest(username="testuser", email="test@example.com", password="Short1")

    def test_password_no_uppercase(self):
        """Password without uppercase should be rejected."""
        with pytest.raises(ValidationError):
            RegisterRequest(username="testuser", email="test@example.com", password="testpass123")

    def test_password_no_lowercase(self):
        """Password without lowercase should be rejected."""
        with pytest.raises(ValidationError):
            RegisterRequest(username="testuser", email="test@example.com", password="TESTPASS123")

    def test_password_no_digit(self):
        """Password without digits should be rejected."""
        with pytest.raises(ValidationError):
            RegisterRequest(username="testuser", email="test@example.com", password="TestPassword")


class TestLoginRequest:
    """Tests for LoginRequest schema."""

    def test_valid_login(self):
        """Valid login should be accepted."""
        req = LoginRequest(username="testuser", password="password123")
        assert req.username == "testuser"

    def test_empty_username_rejected(self):
        """Empty username should be rejected."""
        with pytest.raises(ValidationError):
            LoginRequest(username="", password="password123")

    def test_empty_password_rejected(self):
        """Empty password should be rejected."""
        with pytest.raises(ValidationError):
            LoginRequest(username="testuser", password="")


class TestExportRequest:
    """Tests for ExportRequest schema."""

    def test_valid_export_pdf(self):
        """Valid PDF export should be accepted."""
        req = ExportRequest(data=[{"col1": "value1"}], format=ExportFormat.PDF, title="Test Report")
        assert req.format == ExportFormat.PDF

    def test_valid_export_excel(self):
        """Valid Excel export should be accepted."""
        req = ExportRequest(data=[{"col1": "value1"}], format=ExportFormat.EXCEL)
        assert req.format == ExportFormat.EXCEL

    def test_empty_data_rejected(self):
        """Empty data should be rejected."""
        with pytest.raises(ValidationError):
            ExportRequest(data=[], format=ExportFormat.CSV)

    def test_invalid_format_rejected(self):
        """Invalid format should be rejected."""
        with pytest.raises(ValidationError):
            ExportRequest(data=[{"col1": "value1"}], format="invalid_format")


class TestDashboardCreateRequest:
    """Tests for DashboardCreateRequest schema."""

    def test_valid_dashboard(self):
        """Valid dashboard request should be accepted."""
        req = DashboardCreateRequest(data=[{"x": 1, "y": 2}], title="Test Dashboard")
        assert req.title == "Test Dashboard"

    def test_empty_data_rejected(self):
        """Empty data should be rejected."""
        with pytest.raises(ValidationError):
            DashboardCreateRequest(data=[], title="Empty Dashboard")

    def test_auto_generate_default(self):
        """Auto-generate should default to True."""
        req = DashboardCreateRequest(data=[{"x": 1}])
        assert req.auto_generate is True


class TestEnums:
    """Tests for enum types."""

    def test_export_format_values(self):
        """ExportFormat should have expected values."""
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.EXCEL.value == "excel"
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.HTML.value == "html"
        assert ExportFormat.JSON.value == "json"

    def test_chart_type_values(self):
        """ChartType should have expected values."""
        assert ChartType.BAR.value == "bar"
        assert ChartType.LINE.value == "line"
        assert ChartType.PIE.value == "pie"


class TestHealthCheckResponse:
    """Tests for HealthCheckResponse schema."""

    def test_default_values(self):
        """Health check should have correct defaults."""
        resp = HealthCheckResponse(version="1.0.0")
        assert resp.status == "healthy"
        assert resp.database == "connected"
        assert resp.ai_service == "available"


class TestSavedQuery:
    """Tests for SavedQuery schema."""

    def test_valid_saved_query(self):
        """Valid saved query should be accepted."""
        query = SavedQuery(name="Customer Count", question="How many customers?", sql="SELECT COUNT(*) FROM customers")
        assert query.use_count == 0

    def test_name_too_long_rejected(self):
        """Name over 100 characters should be rejected."""
        with pytest.raises(ValidationError):
            SavedQuery(name="x" * 101, question="test", sql="SELECT 1")

    def test_negative_use_count_rejected(self):
        """Negative use count should be rejected."""
        with pytest.raises(ValidationError):
            SavedQuery(name="Test", question="test", sql="SELECT 1", use_count=-1)


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_basic_error(self):
        """Basic error should be accepted."""
        resp = ErrorResponse(error="Something went wrong")
        assert resp.error == "Something went wrong"
        assert resp.suggestion is None

    def test_error_with_sql(self):
        """Error with SQL should be accepted."""
        resp = ErrorResponse(
            error="SQL syntax error", generated_sql="SELECT * FORM customers", suggestion="Check spelling of 'FROM'"
        )
        assert resp.generated_sql is not None
