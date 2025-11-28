"""
DataPulse Database Manager
==========================

Gestisce sessioni utente e database personalizzati.
Permette il caricamento di file CSV/Excel e SQLite.

Author: DataPulse Team
License: MIT
"""

import os
import uuid
import shutil
import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List, Any
from pathlib import Path

logger = logging.getLogger("datapulse.db_manager")

# ============================================================================
# CONFIGURAZIONE
# ============================================================================

# Directory per i database degli utenti
BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"

# Crea directory se non esistono
UPLOADS_DIR.mkdir(exist_ok=True)

# Durata sessione (4 ore)
SESSION_TTL = timedelta(hours=4)

# Dimensione massima file (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


# ============================================================================
# SESSION MANAGER
# ============================================================================

class SessionManager:
    """
    Gestisce le sessioni utente e i loro database personalizzati.
    
    Ogni sessione ha:
    - Un ID univoco (UUID)
    - Un database SQLite (demo o caricato dall'utente)
    - Schema del database
    - Timestamp creazione/ultimo accesso
    """
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self._cleanup_old_sessions()
    
    def create_session(self) -> str:
        """Crea una nuova sessione con il database demo."""
        session_id = str(uuid.uuid4())
        demo_db_path = DATA_DIR / "database.db"
        
        self.sessions[session_id] = {
            "id": session_id,
            "db_path": str(demo_db_path),
            "db_type": "demo",
            "schema": self._get_demo_schema(),
            "tables": ["customers", "products", "orders", "order_items"],
            "created_at": datetime.now(),
            "last_access": datetime.now()
        }
        
        logger.info(f"Nuova sessione creata: {session_id[:8]}... (demo)")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Recupera una sessione esistente."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Verifica scadenza
        if datetime.now() - session["created_at"] > SESSION_TTL:
            self.delete_session(session_id)
            return None
        
        # Aggiorna ultimo accesso
        session["last_access"] = datetime.now()
        return session
    
    def delete_session(self, session_id: str):
        """Elimina una sessione e i suoi file."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Elimina file database se non è il demo
            if session["db_type"] != "demo":
                session_dir = UPLOADS_DIR / session_id
                if session_dir.exists():
                    shutil.rmtree(session_dir)
            
            del self.sessions[session_id]
            logger.info(f"Sessione eliminata: {session_id[:8]}...")
    
    def upload_csv(self, session_id: str, files: List[Tuple[str, bytes]]) -> Tuple[bool, str]:
        """
        Carica file CSV e crea un database SQLite.
        
        Args:
            session_id: ID della sessione
            files: Lista di tuple (nome_file, contenuto_bytes)
        
        Returns:
            (success, message)
        """
        if session_id not in self.sessions:
            return False, "Sessione non valida"
        
        # Crea directory sessione
        session_dir = UPLOADS_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Crea database SQLite
        db_path = session_dir / "user_database.db"
        
        try:
            conn = sqlite3.connect(str(db_path))
            tables_created = []
            
            for filename, content in files:
                # Determina nome tabella dal nome file
                table_name = self._sanitize_table_name(filename)
                
                # Leggi CSV/Excel
                try:
                    if filename.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(pd.io.common.BytesIO(content))
                    else:
                        # Prova diversi encoding
                        try:
                            df = pd.read_csv(pd.io.common.BytesIO(content), encoding='utf-8')
                        except UnicodeDecodeError:
                            df = pd.read_csv(pd.io.common.BytesIO(content), encoding='latin-1')
                except Exception as e:
                    conn.close()
                    return False, f"Errore lettura file {filename}: {str(e)}"
                
                # Pulisci nomi colonne
                df.columns = [self._sanitize_column_name(col) for col in df.columns]
                
                # Scrivi nel database
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                tables_created.append(table_name)
                logger.info(f"Tabella creata: {table_name} ({len(df)} righe, {len(df.columns)} colonne)")
            
            conn.close()
            
            # Aggiorna sessione
            schema = self._extract_schema(str(db_path))
            self.sessions[session_id].update({
                "db_path": str(db_path),
                "db_type": "custom",
                "schema": schema,
                "tables": tables_created,
                "last_access": datetime.now()
            })
            
            return True, f"Database creato con {len(tables_created)} tabelle: {', '.join(tables_created)}"
            
        except Exception as e:
            logger.error(f"Errore creazione database: {str(e)}")
            return False, f"Errore creazione database: {str(e)}"
    
    def upload_sqlite(self, session_id: str, filename: str, content: bytes) -> Tuple[bool, str]:
        """
        Carica un file SQLite esistente.
        
        Args:
            session_id: ID della sessione
            filename: Nome del file
            content: Contenuto del file in bytes
        
        Returns:
            (success, message)
        """
        if session_id not in self.sessions:
            return False, "Sessione non valida"
        
        # Crea directory sessione
        session_dir = UPLOADS_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        
        db_path = session_dir / "user_database.db"
        
        try:
            # Salva file
            with open(db_path, 'wb') as f:
                f.write(content)
            
            # Verifica che sia un database SQLite valido
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not tables:
                os.remove(db_path)
                return False, "Il database non contiene tabelle"
            
            # Estrai schema
            schema = self._extract_schema(str(db_path))
            
            # Aggiorna sessione
            self.sessions[session_id].update({
                "db_path": str(db_path),
                "db_type": "custom",
                "schema": schema,
                "tables": tables,
                "last_access": datetime.now()
            })
            
            return True, f"Database caricato con {len(tables)} tabelle: {', '.join(tables)}"
            
        except sqlite3.Error as e:
            if db_path.exists():
                os.remove(db_path)
            return False, f"File non valido: non è un database SQLite valido ({str(e)})"
        except Exception as e:
            logger.error(f"Errore caricamento SQLite: {str(e)}")
            return False, f"Errore caricamento: {str(e)}"
    
    def reset_to_demo(self, session_id: str) -> Tuple[bool, str]:
        """Resetta la sessione al database demo."""
        if session_id not in self.sessions:
            return False, "Sessione non valida"
        
        session = self.sessions[session_id]
        
        # Elimina file custom se esiste
        if session["db_type"] != "demo":
            session_dir = UPLOADS_DIR / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
        
        # Resetta a demo
        demo_db_path = DATA_DIR / "database.db"
        session.update({
            "db_path": str(demo_db_path),
            "db_type": "demo",
            "schema": self._get_demo_schema(),
            "tables": ["customers", "products", "orders", "order_items"],
            "last_access": datetime.now()
        })
        
        return True, "Database resettato al demo"
    
    def _sanitize_table_name(self, filename: str) -> str:
        """Crea un nome tabella valido dal nome file."""
        import re
        # Rimuovi estensione
        name = Path(filename).stem
        # Sostituisci caratteri non validi
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Assicura che inizi con lettera
        if name and name[0].isdigit():
            name = 'table_' + name
        return name.lower()[:50] or 'table'
    
    def _sanitize_column_name(self, col: str) -> str:
        """Crea un nome colonna valido."""
        import re
        col = str(col).strip()
        col = re.sub(r'[^a-zA-Z0-9_]', '_', col)
        if col and col[0].isdigit():
            col = 'col_' + col
        return col.lower()[:50] or 'column'
    
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
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["created_at"] > SESSION_TTL
        ]
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
