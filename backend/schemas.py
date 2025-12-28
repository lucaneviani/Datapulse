"""
DataPulse Pydantic Schemas Module

Centralized request/response models for the FastAPI application.
Provides type validation, documentation, and serialization.

B3: Centralized Pydantic Schemas - Architectural Improvement

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


# =============================================================================
# ENUMS
# =============================================================================

class ExportFormat(str, Enum):
    """Supported export formats."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"
    JSON = "json"


class ChartType(str, Enum):
    """Supported chart types for dashboards."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"


class DatabaseType(str, Enum):
    """Supported database types."""
    DEMO = "demo"
    CUSTOM = "custom"


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class BaseResponse(BaseModel):
    """Base response schema with common fields."""
    success: bool = Field(default=True, description="Request success status")
    message: Optional[str] = Field(default=None, description="Status message")
    
    model_config = ConfigDict(
        from_attributes=True,  # SQLAlchemy ORM compatibility
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ANALYZE SCHEMAS
# =============================================================================

class AnalyzeRequest(BaseModel):
    """Request schema for the /api/analyze endpoint."""
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        description="Natural language question to convert to SQL",
        examples=["How many customers are there?", "What are the total sales by region?"]
    )
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate and sanitize question input."""
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty or whitespace only")
        # Basic XSS prevention
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError("Invalid characters in question")
        return v


class AnalyzeResponse(BaseModel):
    """Success response schema for /api/analyze."""
    generated_sql: str = Field(..., description="AI-generated SQL query")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    row_count: int = Field(default=0, ge=0, description="Number of rows returned")
    execution_time_ms: Optional[float] = Field(default=None, description="Query execution time")
    cached: Optional[bool] = Field(default=False, description="Whether result was from cache")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "generated_sql": "SELECT COUNT(*) AS total FROM customers",
                "data": [{"total": 793}],
                "row_count": 1,
                "execution_time_ms": 12.5,
                "cached": False
            }
        }
    )


class AnalyzeSessionRequest(BaseModel):
    """Request for session-based analysis (custom databases)."""
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        description="Natural language question"
    )
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        return AnalyzeRequest.validate_question(v)


# =============================================================================
# ERROR SCHEMAS
# =============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code for programmatic handling")
    field: Optional[str] = Field(default=None, description="Field that caused the error")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    generated_sql: Optional[str] = Field(default=None, description="Generated SQL if available")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix")
    details: Optional[List[ErrorDetail]] = Field(default=None, description="Detailed errors")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Invalid SQL syntax",
                "generated_sql": "SELECT * FORM customers",
                "suggestion": "Check the table name spelling",
                "details": [
                    {"code": "SQL_SYNTAX", "message": "Unknown keyword 'FORM'"}
                ]
            }
        }
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response (422)."""
    detail: List[Dict[str, Any]] = Field(..., description="Validation error details")


# =============================================================================
# AUTHENTICATION SCHEMAS
# =============================================================================

class RegisterRequest(BaseModel):
    """User registration request schema."""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        pattern=r'^[a-zA-Z0-9_]+$',
        description="Username (alphanumeric and underscores only)"
    )
    email: str = Field(
        ..., 
        min_length=5, 
        max_length=254,  # RFC 5321
        description="Valid email address"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="Password (minimum 8 characters)"
    )
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Basic email format validation."""
        import re
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        v = v.strip().lower()
        if not email_regex.match(v):
            raise ValueError("Invalid email format")
        if '..' in v:
            raise ValueError("Invalid email: consecutive dots")
        local, _, domain = v.partition('@')
        if local.startswith('.') or local.endswith('.'):
            raise ValueError("Invalid email format")
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """User login request schema."""
    username: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Username or email"
    )
    password: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Password"
    )


class AuthResponse(BaseModel):
    """Authentication response with tokens."""
    success: bool = Field(..., description="Login/register success")
    message: str = Field(..., description="Status message")
    access_token: Optional[str] = Field(default=None, description="JWT access token")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(default=None, description="Token expiry in seconds")
    user: Optional[Dict[str, Any]] = Field(default=None, description="User info")


class TokenRefreshRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str = Field(..., description="Valid refresh token")


class UserProfile(BaseModel):
    """User profile response schema."""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    name: Optional[str] = Field(default=None, description="Display name")
    created_at: Optional[str] = Field(default=None, description="Registration date")
    last_login: Optional[str] = Field(default=None, description="Last login time")


# =============================================================================
# EXPORT SCHEMAS
# =============================================================================

class ExportRequest(BaseModel):
    """Data export request schema."""
    data: List[Dict[str, Any]] = Field(
        ..., 
        min_length=1,
        description="Data to export (non-empty array)"
    )
    format: ExportFormat = Field(
        ..., 
        description="Output format: pdf, excel, csv, html, json"
    )
    title: str = Field(
        default="Report DataPulse", 
        max_length=200,
        description="Report title"
    )
    query: Optional[str] = Field(
        default=None, 
        max_length=1000,
        description="SQL query executed"
    )
    include_charts: bool = Field(
        default=False,
        description="Include data visualizations"
    )
    
    @field_validator('data')
    @classmethod
    def validate_data_not_empty(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not v:
            raise ValueError("Data cannot be empty")
        return v


class ExportResponse(BaseModel):
    """Export operation response."""
    success: bool = Field(..., description="Export success status")
    filename: Optional[str] = Field(default=None, description="Generated filename")
    download_url: Optional[str] = Field(default=None, description="Download URL")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# DASHBOARD SCHEMAS
# =============================================================================

class ChartConfig(BaseModel):
    """Configuration for a dashboard chart."""
    type: ChartType = Field(..., description="Chart type")
    x_column: str = Field(..., description="X-axis column")
    y_column: str = Field(..., description="Y-axis column")
    title: Optional[str] = Field(default=None, description="Chart title")
    color_column: Optional[str] = Field(default=None, description="Color grouping column")


class DashboardCreateRequest(BaseModel):
    """Dashboard creation request schema."""
    data: List[Dict[str, Any]] = Field(
        ..., 
        min_length=1,
        description="Data to analyze"
    )
    title: str = Field(
        default="Dashboard", 
        max_length=200,
        description="Dashboard title"
    )
    charts: Optional[List[ChartConfig]] = Field(
        default=None,
        description="Chart configurations"
    )
    auto_generate: bool = Field(
        default=True,
        description="Auto-generate chart suggestions"
    )
    
    @field_validator('data')
    @classmethod
    def validate_dashboard_data(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not v:
            raise ValueError("Dashboard data cannot be empty")
        return v


class DashboardResponse(BaseModel):
    """Dashboard generation response."""
    success: bool = Field(..., description="Dashboard creation success")
    charts: Optional[List[Dict[str, Any]]] = Field(default=None, description="Generated charts")
    suggestions: Optional[List[str]] = Field(default=None, description="AI suggestions")
    error: Optional[str] = Field(default=None, description="Error message")


# =============================================================================
# SESSION/DATABASE SCHEMAS
# =============================================================================

class SessionCreateResponse(BaseModel):
    """Response when creating a new database session."""
    session_id: str = Field(..., description="Unique session identifier (UUID4)")
    database_type: DatabaseType = Field(..., description="Database type")
    message: str = Field(..., description="Status message")


class SessionInfoResponse(BaseModel):
    """Information about an active session."""
    session_id: str = Field(..., description="Session ID")
    database_path: Optional[str] = Field(default=None, description="Database path (masked)")
    tables: List[str] = Field(default_factory=list, description="Available tables")
    created_at: Optional[str] = Field(default=None, description="Session creation time")


class DatabaseUploadRequest(BaseModel):
    """Database file upload metadata."""
    filename: str = Field(..., max_length=255, description="Original filename")
    file_size: int = Field(..., ge=1, le=100_000_000, description="File size in bytes (max 100MB)")


class SchemaResponse(BaseModel):
    """Database schema information."""
    tables: Dict[str, List[Dict[str, str]]] = Field(
        ..., 
        description="Tables with their columns and types"
    )
    row_counts: Optional[Dict[str, int]] = Field(
        default=None,
        description="Row count per table"
    )


# =============================================================================
# QUERY HISTORY SCHEMAS
# =============================================================================

class SavedQuery(BaseModel):
    """Saved query schema."""
    id: Optional[int] = Field(default=None, description="Query ID")
    name: str = Field(..., min_length=1, max_length=100, description="Query name")
    question: str = Field(..., description="Natural language question")
    sql: str = Field(..., description="Generated SQL")
    user_id: Optional[int] = Field(default=None, description="Owner user ID")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    use_count: int = Field(default=0, ge=0, description="Usage count")


class QueryHistoryResponse(BaseModel):
    """Query history list response."""
    queries: List[SavedQuery] = Field(default_factory=list, description="Saved queries")
    total: int = Field(default=0, ge=0, description="Total query count")


# =============================================================================
# HEALTH/STATUS SCHEMAS
# =============================================================================

class HealthCheckResponse(BaseModel):
    """API health check response."""
    status: str = Field(default="healthy", description="API status")
    version: str = Field(..., description="API version")
    database: str = Field(default="connected", description="Database status")
    ai_service: str = Field(default="available", description="AI service status")
    uptime_seconds: Optional[float] = Field(default=None, description="Server uptime")


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    cache_size: int = Field(..., ge=0, description="Current cache entries")
    max_size: int = Field(..., ge=0, description="Maximum cache size")
    hit_rate: Optional[float] = Field(default=None, ge=0, le=1, description="Cache hit rate")


# =============================================================================
# I18N SCHEMAS
# =============================================================================

class TranslationRequest(BaseModel):
    """Request for text translation."""
    text: str = Field(..., description="Text to translate")
    source_lang: str = Field(default="auto", description="Source language code")
    target_lang: str = Field(..., description="Target language code")


class LanguageInfo(BaseModel):
    """Language information."""
    code: str = Field(..., description="Language code (ISO 639-1)")
    name: str = Field(..., description="Language name in English")
    native_name: str = Field(..., description="Language name in native language")
    rtl: bool = Field(default=False, description="Right-to-left script")


# =============================================================================
# PAGINATION SCHEMAS
# =============================================================================

class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: str = Field(default="asc", pattern=r'^(asc|desc)$', description="Sort order")


class PaginatedResponse(BaseModel):
    """Base paginated response."""
    items: List[Any] = Field(default_factory=list, description="Page items")
    total: int = Field(..., ge=0, description="Total item count")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total page count")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


# =============================================================================
# TYPE ALIASES FOR BACKWARD COMPATIBILITY
# =============================================================================

# These aliases ensure existing code using the old names still works
Request = AnalyzeRequest
Response = AnalyzeResponse
Error = ErrorResponse
