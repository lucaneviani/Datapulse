"""
DataPulse Authentication System
===============================

Sistema di autenticazione con JWT per gestire utenti e sessioni persistenti.

Features:
- Registrazione utenti con email/password
- Login con generazione JWT token
- Protezione endpoint con decoratori
- Refresh token per sessioni lunghe
- Gestione profili utente

Author: DataPulse Team
License: MIT
"""

import os
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

import jwt
from pydantic import BaseModel, EmailStr, Field
import sqlite3

logger = logging.getLogger("datapulse.auth")

# ============================================================================
# CONFIGURAZIONE
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
AUTH_DB_PATH = BASE_DIR / "data" / "users.db"

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password requirements
MIN_PASSWORD_LENGTH = 8


# ============================================================================
# MODELLI PYDANTIC
# ============================================================================

class UserCreate(BaseModel):
    """Schema per registrazione utente."""
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)


class UserLogin(BaseModel):
    """Schema per login utente."""
    email: str
    password: str


class UserResponse(BaseModel):
    """Schema risposta utente (senza password)."""
    id: int
    email: str
    name: str
    created_at: str
    is_active: bool


class TokenResponse(BaseModel):
    """Schema risposta token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    """Profilo utente completo."""
    id: int
    email: str
    name: str
    created_at: str
    last_login: Optional[str]
    saved_queries_count: int
    dashboards_count: int


# ============================================================================
# DATABASE UTENTI
# ============================================================================

def init_auth_database():
    """Inizializza il database degli utenti."""
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
    logger.info("Database autenticazione inizializzato")


# Inizializza DB all'import
init_auth_database()


# ============================================================================
# FUNZIONI PASSWORD
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password con salt."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    )
    return f"{salt}${pwdhash.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica password contro hash."""
    try:
        salt, stored_hash = password_hash.split('$')
        pwdhash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        )
        return pwdhash.hex() == stored_hash
    except:
        return False


# ============================================================================
# FUNZIONI JWT
# ============================================================================

def create_access_token(user_id: int, email: str) -> str:
    """Crea JWT access token."""
    expires = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expires,
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> Tuple[str, datetime]:
    """Crea refresh token e lo salva nel DB."""
    expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
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
    """Verifica e decodifica access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token scaduto")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token non valido: {e}")
        return None


def verify_refresh_token(token: str) -> Optional[int]:
    """Verifica refresh token e restituisce user_id."""
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
    
    if datetime.fromisoformat(expires_at) < datetime.utcnow():
        return None
    
    return user_id


def revoke_refresh_token(token: str):
    """Revoca un refresh token."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("UPDATE refresh_tokens SET revoked = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ============================================================================
# GESTIONE UTENTI
# ============================================================================

def create_user(email: str, password: str, name: str) -> Tuple[bool, str, Optional[int]]:
    """
    Crea un nuovo utente.
    
    Returns:
        (success, message, user_id)
    """
    # Validazione
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password deve avere almeno {MIN_PASSWORD_LENGTH} caratteri", None
    
    if "@" not in email or "." not in email:
        return False, "Email non valida", None
    
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
        logger.info(f"Nuovo utente creato: {email}")
        return True, "Utente creato con successo", user_id
    except sqlite3.IntegrityError:
        return False, "Email già registrata", None
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Autentica un utente.
    
    Returns:
        (success, message, user_data)
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
        return False, "Email non trovata", None
    
    user_id, user_email, password_hash, name, is_active = result
    
    if not is_active:
        conn.close()
        return False, "Account disattivato", None
    
    if not verify_password(password, password_hash):
        conn.close()
        return False, "Password errata", None
    
    # Aggiorna last_login
    cursor.execute(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), user_id)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"Login riuscito: {email}")
    return True, "Login effettuato", {
        "id": user_id,
        "email": user_email,
        "name": name
    }


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Ottiene dati utente per ID."""
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
    """Ottiene profilo completo utente con statistiche."""
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


# ============================================================================
# QUERY SALVATE
# ============================================================================

def save_query(user_id: int, name: str, question: str, sql_query: str = None) -> Tuple[bool, str, Optional[int]]:
    """Salva una query per l'utente."""
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
        (datetime.utcnow().isoformat(), query_id)
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
