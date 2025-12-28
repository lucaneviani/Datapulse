"""
DataPulse Authentication Module

JWT-based authentication system for user management and session handling.

Features:
    - User registration with email/password
    - JWT token generation and validation
    - Refresh tokens for extended sessions
    - Password hashing with bcrypt
    - User profile management

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import os
import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

import jwt
from pydantic import BaseModel, EmailStr, Field
import sqlite3

logger = logging.getLogger("datapulse.auth")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
AUTH_DB_PATH = BASE_DIR / "data" / "users.db"
SECRET_KEY_FILE = BASE_DIR / "data" / ".jwt_secret"

# JWT Configuration - Persistent secret key
def _get_or_create_secret_key() -> str:
    """Get JWT secret from env, file, or generate and persist a new one."""
    # Priority 1: Environment variable
    env_key = os.getenv("JWT_SECRET_KEY")
    if env_key and len(env_key) >= 32:
        return env_key
    
    # Priority 2: Persisted secret file
    if SECRET_KEY_FILE.exists():
        try:
            return SECRET_KEY_FILE.read_text().strip()
        except Exception:
            pass
    
    # Priority 3: Generate and persist new secret
    new_key = secrets.token_hex(32)
    try:
        SECRET_KEY_FILE.parent.mkdir(exist_ok=True)
        SECRET_KEY_FILE.write_text(new_key)
        
        # A4: Cross-platform file permission handling
        import platform
        if platform.system() != 'Windows':
            # Unix: Set restrictive permissions
            SECRET_KEY_FILE.chmod(0o600)  # Read/write only for owner
        else:
            # Windows: Use icacls to restrict access (best effort)
            try:
                import subprocess
                # Remove inheritance and grant only current user access
                subprocess.run(
                    ['icacls', str(SECRET_KEY_FILE), '/inheritance:r', '/grant:r', f'{os.getlogin()}:F'],
                    capture_output=True, check=False
                )
            except Exception:
                pass  # Best effort on Windows
        
        logger.warning("Generated new JWT secret key and saved to .jwt_secret")
    except Exception as e:
        logger.warning(f"Could not persist JWT secret: {e}. Key will be regenerated on restart.")
    
    return new_key

SECRET_KEY = _get_or_create_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password requirements
MIN_PASSWORD_LENGTH = 8


# -----------------------------------------------------------------------------
# Pydantic Models
# -----------------------------------------------------------------------------

class UserCreate(BaseModel):
    """User registration request schema."""
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)


class UserLogin(BaseModel):
    """User login request schema."""
    email: str
    password: str


class UserResponse(BaseModel):
    """User response schema (excludes password)."""
    id: int
    email: str
    name: str
    created_at: str
    is_active: bool


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    """Complete user profile schema."""
    id: int
    email: str
    name: str
    created_at: str
    last_login: Optional[str]
    saved_queries_count: int
    dashboards_count: int


# -----------------------------------------------------------------------------
# User Database
# -----------------------------------------------------------------------------

def init_auth_database():
    """Initialize the users database and create required tables."""
    AUTH_DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    
    # Tabella utenti
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Tabella refresh tokens
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Tabella query salvate
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            question TEXT NOT NULL,
            sql_query TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            use_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Tabella dashboard salvate
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            config TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            is_default BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Tabella database utente
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_databases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            schema_info TEXT,
            tables_list TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Authentication database initialized")


# Initialize DB on import
init_auth_database()


# -----------------------------------------------------------------------------
# Password Hashing
# -----------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC with random salt."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    )
    return f"{salt}${pwdhash.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, stored_hash = password_hash.split('$')
        pwdhash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        )
        return pwdhash.hex() == stored_hash
    except (ValueError, AttributeError, TypeError):
        return False


# -----------------------------------------------------------------------------
# JWT Token Management
# -----------------------------------------------------------------------------

def create_access_token(user_id: int, email: str) -> str:
    """Create JWT access token."""
    expires = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expires,
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> Tuple[str, datetime]:
    """Create refresh token and store in database."""
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token = secrets.token_urlsafe(64)
    
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires.isoformat())
    )
    conn.commit()
    conn.close()
    
    return token, expires


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def verify_refresh_token(token: str) -> Optional[int]:
    """Verify refresh token and return user_id."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """SELECT user_id, expires_at, revoked FROM refresh_tokens 
           WHERE token = ?""",
        (token,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    user_id, expires_at, revoked = result
    
    if revoked:
        return None
    
    if datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None
    
    return user_id


def revoke_refresh_token(token: str):
    """Revoke a refresh token."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("UPDATE refresh_tokens SET revoked = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# -----------------------------------------------------------------------------
# Email Validation (A5 Enhancement)
# -----------------------------------------------------------------------------

import re

# RFC 5322 simplified email regex pattern
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format.
    
    Args:
        email: Email to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    email = email.strip().lower()
    
    if len(email) < 5:
        return False, "Email too short"
    
    if len(email) > 254:  # RFC 5321 max length
        return False, "Email too long"
    
    if not EMAIL_REGEX.match(email):
        return False, "Invalid email format"
    
    # Check for common invalid patterns
    if ".." in email:
        return False, "Invalid email: consecutive dots"
    
    # Check domain has at least one dot
    local, _, domain = email.partition("@")
    
    # Local part validation
    if local.startswith(".") or local.endswith("."):
        return False, "Invalid email: local part starts or ends with dot"
    
    # Domain validation
    if domain.startswith(".") or domain.endswith("."):
        return False, "Invalid email: domain starts or ends with dot"
    
    if "." not in domain:
        return False, "Invalid email: invalid domain"
    
    return True, "OK"


# -----------------------------------------------------------------------------
# User Management
# -----------------------------------------------------------------------------

def create_user(email: str, password: str, name: str) -> Tuple[bool, str, Optional[int]]:
    """
    Create a new user.
    
    Returns:
        Tuple of (success, message, user_id)
    """
    # A5: Enhanced email validation
    email_valid, email_error = validate_email(email)
    if not email_valid:
        return False, email_error, None
    
    # Password validation
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters", None
    
    password_hash = hash_password(password)
    
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (email.lower().strip(), password_hash, name.strip())
        )
        user_id = cursor.lastrowid
        conn.commit()
        logger.info(f"New user created: {email}")
        return True, "User created successfully", user_id
    except sqlite3.IntegrityError:
        return False, "Email already registered", None
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Authenticate a user.
    
    Returns:
        Tuple of (success, message, user_data)
    """
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, password_hash, name, is_active FROM users WHERE email = ?",
        (email.lower().strip(),)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "Email not found", None
    
    user_id, user_email, password_hash, name, is_active = result
    
    if not is_active:
        conn.close()
        return False, "Account deactivated", None
    
    if not verify_password(password, password_hash):
        conn.close()
        return False, "Incorrect password", None
    
    # Update last_login
    cursor.execute(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), user_id)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"Login successful: {email}")
    return True, "Login successful", {
        "id": user_id,
        "email": user_email,
        "name": name
    }


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user data by ID."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, name, created_at, last_login, is_active FROM users WHERE id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    return {
        "id": result[0],
        "email": result[1],
        "name": result[2],
        "created_at": result[3],
        "last_login": result[4],
        "is_active": result[5]
    }


def get_user_profile(user_id: int) -> Optional[Dict]:
    """Get complete user profile with statistics."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    
    # Info base
    cursor.execute(
        "SELECT id, email, name, created_at, last_login FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return None
    
    # Conta query salvate
    cursor.execute("SELECT COUNT(*) FROM saved_queries WHERE user_id = ?", (user_id,))
    queries_count = cursor.fetchone()[0]
    
    # Conta dashboard
    cursor.execute("SELECT COUNT(*) FROM dashboards WHERE user_id = ?", (user_id,))
    dashboards_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "id": user[0],
        "email": user[1],
        "name": user[2],
        "created_at": user[3],
        "last_login": user[4],
        "saved_queries_count": queries_count,
        "dashboards_count": dashboards_count
    }


# -----------------------------------------------------------------------------
# Saved Queries
# -----------------------------------------------------------------------------

def save_query(user_id: int, name: str, question: str, sql_query: str = None) -> Tuple[bool, str, Optional[int]]:
    """Save a query for the user."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO saved_queries (user_id, name, question, sql_query) 
               VALUES (?, ?, ?, ?)""",
            (user_id, name, question, sql_query)
        )
        query_id = cursor.lastrowid
        conn.commit()
        return True, "Query salvata", query_id
    except Exception as e:
        return False, str(e), None
    finally:
        conn.close()


def get_saved_queries(user_id: int) -> list:
    """Ottiene le query salvate dell'utente."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, name, question, sql_query, created_at, last_used, use_count 
           FROM saved_queries WHERE user_id = ? ORDER BY created_at DESC""",
        (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0],
            "name": r[1],
            "question": r[2],
            "sql_query": r[3],
            "created_at": r[4],
            "last_used": r[5],
            "use_count": r[6]
        }
        for r in results
    ]


def delete_saved_query(user_id: int, query_id: int) -> bool:
    """Elimina una query salvata."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM saved_queries WHERE id = ? AND user_id = ?",
        (query_id, user_id)
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def increment_query_usage(query_id: int):
    """Incrementa il contatore di utilizzo query."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE saved_queries 
           SET use_count = use_count + 1, last_used = ? 
           WHERE id = ?""",
        (datetime.now(timezone.utc).isoformat(), query_id)
    )
    conn.commit()
    conn.close()


# ============================================================================
# AUTH MANAGER CLASS (Wrapper per main.py)
# ============================================================================

class AuthManager:
    """
    Classe wrapper per le funzioni di autenticazione.
    Fornisce un'interfaccia unificata per main.py.
    """
    
    def __init__(self):
        """Inizializza il manager."""
        init_auth_database()
    
    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, Any]:
        """
        Registra un nuovo utente.
        
        Args:
            username: Nome utente (usato come 'name')
            email: Email
            password: Password
        
        Returns:
            (success, result_or_error)
        """
        success, message, user_id = create_user(email, password, username)
        
        if success and user_id:
            # Genera token
            token = create_access_token(user_id, email)
            
            return True, {
                "user_id": user_id,
                "username": username,
                "email": email,
                "token": token,
                "message": message
            }
        else:
            return False, message
    
    def login_user(self, username: str, password: str) -> Tuple[bool, Any]:
        """
        Effettua il login.
        
        Args:
            username: Username o email (usiamo come email)
            password: Password
        
        Returns:
            (success, result_or_error)
        """
        success, message, user = authenticate_user(username, password)
        
        if not success or not user:
            return False, message
        
        # Genera token
        token = create_access_token(user["id"], user["email"])
        
        return True, {
            "user_id": user["id"],
            "username": user["name"],
            "email": user["email"],
            "token": token
        }
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verifica un token JWT."""
        payload = verify_access_token(token)
        if payload:
            user_id = payload.get("sub")
            user = get_user_by_id(user_id)
            return user
        return None
    
    def get_current_user(self, token: str) -> Optional[Dict]:
        """Ottiene l'utente corrente dal token."""
        return self.verify_token(token)
    
    def logout_user(self, token: str):
        """Logout - revoca il token (best effort)."""
        # Per ora non facciamo nulla, JWT scade naturalmente
        # In futuro potremmo aggiungere una blacklist
        pass


# Istanza singleton
auth_manager = AuthManager()
