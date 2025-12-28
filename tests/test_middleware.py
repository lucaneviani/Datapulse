"""
Tests for DataPulse Error Handling Middleware

B5: Error Handling Middleware - Test Coverage

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.middleware import (
    AIServiceException,
    AuthenticationException,
    AuthorizationException,
    DatabaseException,
    DataPulseException,
    ErrorCategory,
    FileUploadException,
    NotFoundException,
    RateLimitException,
    ValidationException,
    build_error_response,
    get_request_duration,
    get_request_id,
)


class TestErrorCategory:
    """Tests for error categories."""

    def test_all_categories_defined(self):
        """All expected error categories should be defined."""
        assert ErrorCategory.VALIDATION == "VALIDATION_ERROR"
        assert ErrorCategory.AUTHENTICATION == "AUTH_ERROR"
        assert ErrorCategory.AUTHORIZATION == "AUTHORIZATION_ERROR"
        assert ErrorCategory.NOT_FOUND == "NOT_FOUND"
        assert ErrorCategory.DATABASE == "DATABASE_ERROR"
        assert ErrorCategory.AI_SERVICE == "AI_SERVICE_ERROR"
        assert ErrorCategory.RATE_LIMIT == "RATE_LIMIT_ERROR"
        assert ErrorCategory.FILE_UPLOAD == "FILE_UPLOAD_ERROR"
        assert ErrorCategory.INTERNAL == "INTERNAL_ERROR"
        assert ErrorCategory.BAD_REQUEST == "BAD_REQUEST"


class TestDataPulseException:
    """Tests for base DataPulseException."""

    def test_basic_exception(self):
        """Basic exception with message only."""
        exc = DataPulseException("Something went wrong")
        assert exc.message == "Something went wrong"
        assert exc.category == ErrorCategory.INTERNAL
        assert exc.status_code == 500

    def test_exception_with_category(self):
        """Exception with custom category."""
        exc = DataPulseException("Not found", category=ErrorCategory.NOT_FOUND, status_code=404)
        assert exc.category == ErrorCategory.NOT_FOUND
        assert exc.status_code == 404

    def test_exception_with_details(self):
        """Exception with additional details."""
        exc = DataPulseException("Error", details={"field": "email", "value": "invalid"}, suggestion="Check email format")
        assert exc.details["field"] == "email"
        assert exc.suggestion == "Check email format"

    def test_exception_as_exception(self):
        """Exception should be raiseable."""
        with pytest.raises(DataPulseException) as exc:
            raise DataPulseException("Test error")
        assert str(exc.value) == "Test error"


class TestValidationException:
    """Tests for ValidationException."""

    def test_validation_exception(self):
        """Validation exception should have correct defaults."""
        exc = ValidationException("Invalid email", field="email")
        assert exc.status_code == 422
        assert exc.category == ErrorCategory.VALIDATION
        assert exc.details["field"] == "email"

    def test_validation_with_details(self):
        """Validation exception with extra details."""
        exc = ValidationException("Too long", field="name", details={"max_length": 50, "actual": 100})
        assert exc.details["max_length"] == 50
        assert exc.details["actual"] == 100


class TestAuthenticationException:
    """Tests for AuthenticationException."""

    def test_default_message(self):
        """Auth exception should have default message."""
        exc = AuthenticationException()
        assert exc.message == "Authentication required"
        assert exc.status_code == 401
        assert exc.category == ErrorCategory.AUTHENTICATION

    def test_custom_message(self):
        """Auth exception with custom message."""
        exc = AuthenticationException("Token expired")
        assert exc.message == "Token expired"


class TestAuthorizationException:
    """Tests for AuthorizationException."""

    def test_default_message(self):
        """Authorization exception should have default message."""
        exc = AuthorizationException()
        assert exc.message == "Access denied"
        assert exc.status_code == 403
        assert exc.category == ErrorCategory.AUTHORIZATION


class TestNotFoundException:
    """Tests for NotFoundException."""

    def test_resource_only(self):
        """Not found with resource only."""
        exc = NotFoundException("User")
        assert exc.message == "User not found"
        assert exc.status_code == 404

    def test_resource_with_identifier(self):
        """Not found with resource and identifier."""
        exc = NotFoundException("User", identifier="123")
        assert exc.message == "User '123' not found"
        assert exc.details["resource"] == "User"
        assert exc.details["identifier"] == "123"


class TestDatabaseException:
    """Tests for DatabaseException."""

    def test_database_exception(self):
        """Database exception basics."""
        exc = DatabaseException("Connection failed")
        assert exc.status_code == 500
        assert exc.category == ErrorCategory.DATABASE
        assert "query" in exc.suggestion.lower() or "connection" in exc.suggestion.lower()

    def test_with_query(self):
        """Database exception with SQL query."""
        exc = DatabaseException("Syntax error", query="SELECT * FORM users")
        assert exc.details["query"] == "SELECT * FORM users"


class TestAIServiceException:
    """Tests for AIServiceException."""

    def test_ai_service_exception(self):
        """AI service exception basics."""
        exc = AIServiceException("API unavailable")
        assert exc.status_code == 503
        assert exc.category == ErrorCategory.AI_SERVICE

    def test_with_generated_sql(self):
        """AI exception with generated SQL."""
        exc = AIServiceException("Invalid query generated", generated_sql="DROP TABLE users")
        assert exc.details["generated_sql"] == "DROP TABLE users"


class TestRateLimitException:
    """Tests for RateLimitException."""

    def test_rate_limit_default(self):
        """Rate limit with default retry time."""
        exc = RateLimitException()
        assert exc.status_code == 429
        assert exc.details["retry_after_seconds"] == 60

    def test_rate_limit_custom(self):
        """Rate limit with custom retry time."""
        exc = RateLimitException(retry_after=120)
        assert exc.details["retry_after_seconds"] == 120
        assert "120" in exc.suggestion


class TestFileUploadException:
    """Tests for FileUploadException."""

    def test_file_upload_exception(self):
        """File upload exception basics."""
        exc = FileUploadException("File too large")
        assert exc.status_code == 400
        assert exc.category == ErrorCategory.FILE_UPLOAD

    def test_with_filename(self):
        """File upload exception with filename."""
        exc = FileUploadException("Invalid format", filename="test.exe")
        assert exc.details["filename"] == "test.exe"


class TestBuildErrorResponse:
    """Tests for build_error_response function."""

    def test_basic_response(self):
        """Build basic error response."""
        response = build_error_response(
            request_id="abc123", error="Something went wrong", category=ErrorCategory.INTERNAL, status_code=500
        )

        assert response["success"] == False
        assert response["error"]["message"] == "Something went wrong"
        assert response["error"]["category"] == ErrorCategory.INTERNAL
        assert response["error"]["code"] == 500
        assert response["error"]["request_id"] == "abc123"
        assert "timestamp" in response["error"]

    def test_response_with_details(self):
        """Build response with details."""
        response = build_error_response(
            request_id="abc123",
            error="Validation failed",
            category=ErrorCategory.VALIDATION,
            status_code=422,
            details={"field": "email"},
            suggestion="Check email format",
        )

        assert response["error"]["details"]["field"] == "email"
        assert response["error"]["suggestion"] == "Check email format"

    def test_response_with_debug(self):
        """Build response with debug info."""
        response = build_error_response(
            request_id="abc123", error="Error", include_debug=True, debug_info={"traceback": ["line1", "line2"]}
        )

        assert "debug" in response["error"]
        assert response["error"]["debug"]["traceback"] == ["line1", "line2"]

    def test_response_without_debug(self):
        """Debug info should not appear when disabled."""
        response = build_error_response(
            request_id="abc123", error="Error", include_debug=False, debug_info={"traceback": ["line1"]}
        )

        assert "debug" not in response["error"]

    def test_timestamp_format(self):
        """Timestamp should be ISO format."""
        response = build_error_response(request_id="test", error="Error")
        timestamp = response["error"]["timestamp"]
        # Should parse as ISO datetime
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


class TestRequestHelpers:
    """Tests for request helper functions."""

    def test_get_request_id(self):
        """Get request ID from request state."""
        mock_request = MagicMock()
        mock_request.state.request_id = "test-123"

        assert get_request_id(mock_request) == "test-123"

    def test_get_request_id_missing(self):
        """Get request ID when not set returns 'unknown'."""
        mock_request = MagicMock()
        mock_request.state = MagicMock(spec=[])  # No request_id attribute

        assert get_request_id(mock_request) == "unknown"

    def test_get_request_duration(self):
        """Get request duration."""
        import time

        mock_request = MagicMock()
        mock_request.state.start_time = time.time() - 1.5

        duration = get_request_duration(mock_request)
        assert 1.4 < duration < 1.6

    def test_get_request_duration_no_start(self):
        """Get duration when start time not set."""
        mock_request = MagicMock()
        mock_request.state = MagicMock(spec=[])

        assert get_request_duration(mock_request) == 0.0
