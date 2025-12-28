"""
DataPulse Error Handling Middleware

Centralized error handling with structured logging and consistent responses.

B5: Error Handling Middleware - Architectural Improvement

Features:
    - Structured JSON error responses
    - Request ID tracking for debugging
    - Automatic error categorization
    - Security-aware error messages (no stack traces in production)
    - Performance monitoring with request timing

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import logging
import os
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("datapulse.middleware")


# =============================================================================
# ERROR CATEGORIES
# =============================================================================


class ErrorCategory:
    """Error categories for structured error responses."""

    VALIDATION = "VALIDATION_ERROR"
    AUTHENTICATION = "AUTH_ERROR"
    AUTHORIZATION = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    DATABASE = "DATABASE_ERROR"
    AI_SERVICE = "AI_SERVICE_ERROR"
    RATE_LIMIT = "RATE_LIMIT_ERROR"
    FILE_UPLOAD = "FILE_UPLOAD_ERROR"
    INTERNAL = "INTERNAL_ERROR"
    BAD_REQUEST = "BAD_REQUEST"


class DataPulseException(Exception):
    """Base exception for DataPulse application."""

    def __init__(
        self,
        message: str,
        category: str = ErrorCategory.INTERNAL,
        status_code: int = 500,
        details: dict = None,
        suggestion: str = None,
    ):
        self.message = message
        self.category = category
        self.status_code = status_code
        self.details = details or {}
        self.suggestion = suggestion
        super().__init__(message)


class ValidationException(DataPulseException):
    """Input validation errors."""

    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(
            message=message, category=ErrorCategory.VALIDATION, status_code=422, details={"field": field, **(details or {})}
        )


class AuthenticationException(DataPulseException):
    """Authentication failures."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, category=ErrorCategory.AUTHENTICATION, status_code=401)


class AuthorizationException(DataPulseException):
    """Authorization/permission errors."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, category=ErrorCategory.AUTHORIZATION, status_code=403)


class NotFoundException(DataPulseException):
    """Resource not found errors."""

    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(
            message=message,
            category=ErrorCategory.NOT_FOUND,
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class DatabaseException(DataPulseException):
    """Database operation errors."""

    def __init__(self, message: str, query: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            status_code=500,
            details={"query": query} if query else {},
            suggestion="Check your query syntax or database connection",
        )


class AIServiceException(DataPulseException):
    """AI service (Gemini) errors."""

    def __init__(self, message: str, generated_sql: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AI_SERVICE,
            status_code=503,
            details={"generated_sql": generated_sql} if generated_sql else {},
            suggestion="Try rephrasing your question or try again later",
        )


class RateLimitException(DataPulseException):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please wait before retrying.",
            category=ErrorCategory.RATE_LIMIT,
            status_code=429,
            details={"retry_after_seconds": retry_after},
            suggestion=f"Wait {retry_after} seconds before making another request",
        )


class FileUploadException(DataPulseException):
    """File upload errors."""

    def __init__(self, message: str, filename: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.FILE_UPLOAD,
            status_code=400,
            details={"filename": filename} if filename else {},
            suggestion="Check file format and size limits",
        )


# =============================================================================
# ERROR RESPONSE BUILDER
# =============================================================================


def build_error_response(
    request_id: str,
    error: str,
    category: str = ErrorCategory.INTERNAL,
    status_code: int = 500,
    details: dict = None,
    suggestion: str = None,
    include_debug: bool = False,
    debug_info: dict = None,
) -> dict:
    """Build a structured error response."""
    response = {
        "success": False,
        "error": {
            "message": error,
            "category": category,
            "code": status_code,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

    if details:
        response["error"]["details"] = details

    if suggestion:
        response["error"]["suggestion"] = suggestion

    if include_debug and debug_info:
        response["error"]["debug"] = debug_info

    return response


# =============================================================================
# REQUEST TIMING MIDDLEWARE
# =============================================================================


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request timing and add request IDs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request.state.start_time = time.time()

        # Add request ID to response headers
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - request.state.start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        # Log slow requests (>2 seconds)
        if duration > 2.0:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} " f"took {duration:.2f}s [request_id={request_id}]"
            )

        return response


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================


def setup_exception_handlers(app: FastAPI, debug: bool = False):
    """Configure global exception handlers for the FastAPI app."""

    @app.exception_handler(DataPulseException)
    async def datapulse_exception_handler(request: Request, exc: DataPulseException):
        """Handle custom DataPulse exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(f"DataPulseException: {exc.message} " f"[category={exc.category}] [request_id={request_id}]")

        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_response(
                request_id=request_id,
                error=exc.message,
                category=exc.category,
                status_code=exc.status_code,
                details=exc.details,
                suggestion=exc.suggestion,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        request_id = getattr(request.state, "request_id", "unknown")

        # Extract readable error messages
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({"field": field, "message": error["msg"], "type": error["type"]})

        logger.info(f"Validation error: {len(errors)} issues " f"[request_id={request_id}]")

        return JSONResponse(
            status_code=422,
            content=build_error_response(
                request_id=request_id,
                error="Validation failed",
                category=ErrorCategory.VALIDATION,
                status_code=422,
                details={"errors": errors},
                suggestion="Check the request body and try again",
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle standard HTTP exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")

        # Map status codes to categories
        category_map = {
            400: ErrorCategory.BAD_REQUEST,
            401: ErrorCategory.AUTHENTICATION,
            403: ErrorCategory.AUTHORIZATION,
            404: ErrorCategory.NOT_FOUND,
            429: ErrorCategory.RATE_LIMIT,
        }
        category = category_map.get(exc.status_code, ErrorCategory.INTERNAL)

        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_response(
                request_id=request_id, error=str(exc.detail), category=category, status_code=exc.status_code
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")

        # Log the full traceback for debugging
        logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)} " f"[request_id={request_id}]", exc_info=True)

        # Build response (hide details in production)
        error_message = "An internal error occurred"
        debug_info = None

        if debug:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            debug_info = {"exception_type": type(exc).__name__, "traceback": traceback.format_exc().split("\n")}

        return JSONResponse(
            status_code=500,
            content=build_error_response(
                request_id=request_id,
                error=error_message,
                category=ErrorCategory.INTERNAL,
                status_code=500,
                suggestion="Please try again or contact support if the issue persists",
                include_debug=debug,
                debug_info=debug_info,
            ),
        )


# =============================================================================
# MIDDLEWARE SETUP HELPER
# =============================================================================


def setup_middleware(app: FastAPI, debug: bool = None):
    """
    Configure all middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
        debug: Enable debug mode (defaults to DEBUG env var)
    """
    if debug is None:
        debug = os.getenv("DEBUG", "false").lower() == "true"

    # Add request timing middleware
    app.add_middleware(RequestTimingMiddleware)

    # Setup exception handlers
    setup_exception_handlers(app, debug=debug)

    logger.info(f"Middleware configured [debug={'enabled' if debug else 'disabled'}]")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_request_id(request: Request) -> str:
    """Get the request ID from the current request."""
    return getattr(request.state, "request_id", "unknown")


def get_request_duration(request: Request) -> float:
    """Get the elapsed time for the current request in seconds."""
    start_time = getattr(request.state, "start_time", None)
    if start_time:
        return time.time() - start_time
    return 0.0
