"""
DataPulse Database Manager

Manages user sessions and custom database uploads.
Supports CSV, Excel, and SQLite file imports.

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import io
import logging
import os
import shutil
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger("datapulse.db_manager")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# User database directory
BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"

# Create directories if they don't exist
UPLOADS_DIR.mkdir(exist_ok=True)

# Session duration (4 hours)
SESSION_TTL = timedelta(hours=4)

# Maximum file size (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


# -----------------------------------------------------------------------------
# Session Manager
# -----------------------------------------------------------------------------


class SessionManager:
    """
    Manages user sessions and their custom databases.

    Each session has:
    - A unique ID (UUID)
    - A SQLite database (demo or user-uploaded)
    - Database schema
    - Creation/last access timestamps

    Automatic cleanup runs every 30 minutes to remove expired sessions.
    Thread-safe: All session operations are protected by a lock.
    """

    def __init__(self):
        self._lock = threading.Lock()  # Thread-safe access to sessions
        self.sessions: Dict[str, dict] = {}
        self._cleanup_old_sessions()
        self._start_cleanup_scheduler()

    def _start_cleanup_scheduler(self):
        """Start background thread for periodic session cleanup."""
        import threading

        def cleanup_loop():
            while True:
                import time

                time.sleep(1800)  # 30 minutes
                try:
                    self._cleanup_old_sessions()
                except Exception as e:
                    logger.error(f"Session cleanup error: {e}")

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Session cleanup scheduler started (runs every 30 minutes)")

    def create_session(self) -> str:
        """Create a new session with the demo database. Thread-safe."""
        session_id = str(uuid.uuid4())
        demo_db_path = DATA_DIR / "database.db"

        session_data = {
            "id": session_id,
            "db_path": str(demo_db_path),
            "db_type": "demo",
            "schema": self._get_demo_schema(),
            "tables": ["customers", "products", "orders", "order_items"],
            "created_at": datetime.now(),
            "last_access": datetime.now(),
        }

        with self._lock:
            self.sessions[session_id] = session_data

        logger.info(f"New session created: {session_id[:8]}... (demo)")
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve an existing session. Thread-safe."""
        with self._lock:
            if session_id not in self.sessions:
                return None

            session = self.sessions[session_id]

            # Check expiration
            if datetime.now() - session["created_at"] > SESSION_TTL:
                # Release lock before calling delete (which also acquires lock)
                pass
            else:
                # Update last access and return copy
                session["last_access"] = datetime.now()
                return session.copy()  # Return copy to prevent external modification

        # Session expired - delete outside lock to prevent deadlock
        self.delete_session(session_id)
        return None

    def delete_session(self, session_id: str):
        """Delete a session and its files. Thread-safe."""
        session_data = None

        with self._lock:
            if session_id in self.sessions:
                session_data = self.sessions.pop(session_id)

        # File operations outside lock (IO can be slow)
        if session_data and session_data["db_type"] != "demo":
            session_dir = UPLOADS_DIR / session_id
            if session_dir.exists():
                try:
                    shutil.rmtree(session_dir)
                except Exception as e:
                    logger.error(f"Error deleting session dir: {e}")

        if session_data:
            logger.info(f"Session deleted: {session_id[:8]}...")

    def upload_csv(self, session_id: str, files: List[Tuple[str, bytes]]) -> Tuple[bool, str]:
        """
        Upload CSV files and create a SQLite database.

        Args:
            session_id: Session ID
            files: List of tuples (filename, content_bytes)

        Returns:
            (success, message)
        """
        # A3: Validate session_id format to prevent path traversal
        if not self._is_valid_session_id(session_id):
            return False, "Invalid session ID format"

        with self._lock:
            if session_id not in self.sessions:
                return False, "Invalid session"

        # Create session directory using only the validated session_id
        session_dir = UPLOADS_DIR / session_id
        session_dir.mkdir(exist_ok=True)

        # Create SQLite database with fixed name (not user-provided)
        db_path = session_dir / "user_database.db"

        try:
            conn = sqlite3.connect(str(db_path))
            tables_created = []

            for filename, content in files:
                # A3: Sanitize filename - extract only basename and sanitize
                safe_filename = self._secure_filename(filename)
                table_name = self._sanitize_table_name(safe_filename)

                # Read CSV/Excel
                try:
                    if filename.lower().endswith((".xlsx", ".xls")):
                        df = pd.read_excel(io.BytesIO(content))
                    else:
                        # Try different encodings
                        try:
                            df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
                        except UnicodeDecodeError:
                            df = pd.read_csv(io.BytesIO(content), encoding="latin-1")
                except Exception as e:
                    conn.close()
                    return False, f"Error reading file {filename}: {str(e)}"

                # Clean column names
                df.columns = [self._sanitize_column_name(col) for col in df.columns]

                # Write to database
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                tables_created.append(table_name)
                logger.info(f"Table created: {table_name} ({len(df)} rows, {len(df.columns)} columns)")

            conn.close()

            # Update session with lock
            schema = self._extract_schema(str(db_path))
            with self._lock:
                if session_id in self.sessions:
                    self.sessions[session_id].update(
                        {
                            "db_path": str(db_path),
                            "db_type": "custom",
                            "schema": schema,
                            "tables": tables_created,
                            "last_access": datetime.now(),
                        }
                    )

            return True, f"Database created with {len(tables_created)} tables: {', '.join(tables_created)}"

        except Exception as e:
            logger.error(f"Database creation error: {str(e)}")
            return False, f"Database creation error: {str(e)}"

    def upload_sqlite(self, session_id: str, filename: str, content: bytes) -> Tuple[bool, str]:
        """
        Upload an existing SQLite file.

        Args:
            session_id: Session ID
            filename: File name (sanitized, not used for storage)
            content: File content in bytes

        Returns:
            (success, message)
        """
        # A3: Validate session_id format to prevent path traversal
        if not self._is_valid_session_id(session_id):
            return False, "Invalid session ID format"

        with self._lock:
            if session_id not in self.sessions:
                return False, "Invalid session"

        # A3: Use fixed filename, ignore user-provided filename for security
        # Create session directory using only validated session_id
        session_dir = UPLOADS_DIR / session_id
        session_dir.mkdir(exist_ok=True)

        # Fixed database name - user filename is ignored for security
        db_path = session_dir / "user_database.db"

        try:
            # Save file
            with open(db_path, "wb") as f:
                f.write(content)

            # Verify it's a valid SQLite database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            if not tables:
                os.remove(db_path)
                return False, "Database contains no tables"

            # Extract schema
            schema = self._extract_schema(str(db_path))

            # Update session with lock
            with self._lock:
                if session_id in self.sessions:
                    self.sessions[session_id].update(
                        {
                            "db_path": str(db_path),
                            "db_type": "custom",
                            "schema": schema,
                            "tables": tables,
                            "last_access": datetime.now(),
                        }
                    )

            return True, f"Database loaded with {len(tables)} tables: {', '.join(tables)}"

        except sqlite3.Error as e:
            if db_path.exists():
                os.remove(db_path)
            return False, f"Invalid file: not a valid SQLite database ({str(e)})"
        except Exception as e:
            logger.error(f"SQLite upload error: {str(e)}")
            return False, f"Upload error: {str(e)}"

    def reset_to_demo(self, session_id: str) -> Tuple[bool, str]:
        """Reset session to the demo database. Thread-safe."""
        # Validate session_id format
        if not self._is_valid_session_id(session_id):
            return False, "Invalid session ID format"

        session_data = None
        with self._lock:
            if session_id not in self.sessions:
                return False, "Invalid session"
            session_data = self.sessions[session_id].copy()

        # Delete custom files if they exist (outside lock for IO)
        if session_data["db_type"] != "demo":
            session_dir = UPLOADS_DIR / session_id
            if session_dir.exists():
                try:
                    shutil.rmtree(session_dir)
                except Exception as e:
                    logger.error(f"Error cleaning session dir: {e}")

        # Reset to demo with lock
        demo_db_path = DATA_DIR / "database.db"
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].update(
                    {
                        "db_path": str(demo_db_path),
                        "db_type": "demo",
                        "schema": self._get_demo_schema(),
                        "tables": ["customers", "products", "orders", "order_items"],
                        "last_access": datetime.now(),
                    }
                )

        return True, "Database reset to demo"

    def _is_valid_session_id(self, session_id: str) -> bool:
        """
        Validate session ID format to prevent path traversal attacks.

        A valid session ID is a UUID4 format string.
        """
        import re

        if not session_id or not isinstance(session_id, str):
            return False
        # UUID4 pattern: 8-4-4-4-12 hex characters
        uuid_pattern = r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
        return bool(re.match(uuid_pattern, session_id.lower()))

    def _secure_filename(self, filename: str) -> str:
        """
        Secure a filename by removing path components and dangerous characters.

        Prevents path traversal attacks like '../../../etc/passwd'.
        """
        import re

        if not filename:
            return "unnamed"

        # Get only the basename (remove any path components)
        name = os.path.basename(filename)

        # Remove any null bytes
        name = name.replace("\x00", "")

        # Remove path traversal attempts
        name = name.replace("..", "")
        name = name.replace("/", "")
        name = name.replace("\\", "")

        # Keep only safe characters
        name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)

        # Limit length
        if len(name) > 100:
            name = name[:100]

        return name or "unnamed"

    def _sanitize_table_name(self, filename: str) -> str:
        """Crea un nome tabella valido dal nome file."""
        import re

        # Rimuovi estensione
        name = Path(filename).stem
        # Sostituisci caratteri non validi
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Assicura che inizi con lettera
        if name and name[0].isdigit():
            name = "table_" + name
        return name.lower()[:50] or "table"

    def _sanitize_column_name(self, col: str) -> str:
        """Crea un nome colonna valido."""
        import re

        col = str(col).strip()
        col = re.sub(r"[^a-zA-Z0-9_]", "_", col)
        if col and col[0].isdigit():
            col = "col_" + col
        return col.lower()[:50] or "column"

    def _extract_schema(self, db_path: str) -> str:
        """Estrae lo schema del database in formato testuale per l'AI."""
        schema_parts = []

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Ottieni lista tabelle
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                # Ottieni info colonne
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()

                col_info = []
                for col in columns:
                    col_name = col[1]
                    col_type = col[2] or "TEXT"
                    col_info.append(f"{col_name}: {col_type}")

                # Conta righe
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                row_count = cursor.fetchone()[0]

                schema_parts.append(f"Table: {table} ({row_count} rows)")
                schema_parts.append("Columns: " + ", ".join(col_info))
                schema_parts.append("")

            conn.close()

        except Exception as e:
            logger.error(f"Errore estrazione schema: {str(e)}")
            return "Schema non disponibile"

        return "\n".join(schema_parts)

    def _get_demo_schema(self) -> str:
        """Ritorna lo schema del database demo."""
        return """Table: customers (793 rows)
Columns: id: TEXT, name: TEXT, segment: TEXT, country: TEXT, city: TEXT, state: TEXT, postal_code: TEXT, region: TEXT

Table: products
Columns: id: TEXT, name: TEXT, category: TEXT, sub_category: TEXT

Table: orders
Columns: id: TEXT, customer_id: TEXT, order_date: DATE, ship_date: DATE, ship_mode: TEXT, total: REAL

Table: order_items
Columns: id: INTEGER, order_id: TEXT, product_id: TEXT, quantity: INTEGER, sales: REAL, discount: REAL, profit: REAL

RELATIONSHIPS:
- orders.customer_id -> customers.id
- order_items.order_id -> orders.id
- order_items.product_id -> products.id
"""

    def _cleanup_old_sessions(self):
        """Pulisce sessioni scadute e file orfani."""
        now = datetime.now()

        # Pulisci sessioni scadute
        expired = [sid for sid, session in self.sessions.items() if now - session["created_at"] > SESSION_TTL]
        for sid in expired:
            self.delete_session(sid)

        # Pulisci directory orfane
        if UPLOADS_DIR.exists():
            for item in UPLOADS_DIR.iterdir():
                if item.is_dir() and item.name not in self.sessions:
                    try:
                        shutil.rmtree(item)
                        logger.info(f"Directory orfana eliminata: {item.name[:8]}...")
                    except Exception as e:
                        logger.error(f"Errore eliminazione directory: {str(e)}")


# Istanza globale del session manager
session_manager = SessionManager()


# ============================================================================
# FUNZIONI DI UTILITÀ
# ============================================================================


def execute_query_on_session(session_id: str, sql: str, max_rows: int = 1000) -> Tuple[bool, Any]:
    """
    Esegue una query SQL sul database della sessione.

    Args:
        session_id: ID della sessione
        sql: Query SQL da eseguire
        max_rows: Numero massimo di righe da restituire

    Returns:
        (success, data_or_error)
    """
    session = session_manager.get_session(session_id)
    if not session:
        return False, "Sessione non valida o scaduta"

    db_path = session["db_path"]

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(sql)
        rows = cursor.fetchmany(max_rows)

        # Converti in lista di dict
        result = [dict(row) for row in rows]

        conn.close()
        return True, result

    except Exception as e:
        return False, str(e)


def get_session_tables(session_id: str) -> Tuple[bool, Any]:
    """Ottiene la lista delle tabelle della sessione."""
    session = session_manager.get_session(session_id)
    if not session:
        return False, "Sessione non valida"

    return True, session["tables"]


def get_session_schema(session_id: str) -> Tuple[bool, Any]:
    """Ottiene lo schema del database della sessione."""
    session = session_manager.get_session(session_id)
    if not session:
        return False, "Sessione non valida"

    return True, session["schema"]
