"""
DataPulse Dashboard Module

Automatic dashboard generation system for data visualization.

Features:
    - Automatic data analysis for visualization suggestions
    - Predefined widgets (KPI, charts, tables)
    - Customizable layouts
    - Dashboard persistence and loading

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger("datapulse.dashboard")

BASE_DIR = Path(__file__).parent.parent
AUTH_DB_PATH = BASE_DIR / "data" / "users.db"


# -----------------------------------------------------------------------------
# Widget Types
# -----------------------------------------------------------------------------

WIDGET_TYPES = {
    "kpi": {"name": "KPI Card", "description": "Single numeric value with label", "icon": "📊", "min_cols": 1, "min_rows": 1},
    "bar_chart": {"name": "Bar Chart", "description": "Category comparison", "icon": "📊", "min_cols": 2, "min_rows": 2},
    "pie_chart": {"name": "Pie Chart", "description": "Percentage distribution", "icon": "🥧", "min_cols": 2, "min_rows": 2},
    "line_chart": {"name": "Line Chart", "description": "Time series trend", "icon": "📈", "min_cols": 2, "min_rows": 2},
    "table": {"name": "Table", "description": "Tabular data", "icon": "📋", "min_cols": 2, "min_rows": 2},
    "scatter": {"name": "Scatter Plot", "description": "Variable correlation", "icon": "⚬", "min_cols": 2, "min_rows": 2},
}


# -----------------------------------------------------------------------------
# Automatic Data Analysis
# -----------------------------------------------------------------------------


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze a DataFrame and suggest appropriate visualizations.

    Returns:
        Dict with column info, types, and suggested widgets
    """
    if df is None or df.empty:
        return {"error": "Empty DataFrame"}

    analysis = {"rows": len(df), "columns": len(df.columns), "column_info": [], "suggested_widgets": [], "data_profile": {}}

    numeric_cols = []
    categorical_cols = []
    date_cols = []

    for col in df.columns:
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "unique_count": int(df[col].nunique()),
        }

        # Classifica colonna
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["type"] = "numeric"
            col_info["min"] = float(df[col].min()) if not df[col].isnull().all() else None
            col_info["max"] = float(df[col].max()) if not df[col].isnull().all() else None
            col_info["mean"] = float(df[col].mean()) if not df[col].isnull().all() else None
            numeric_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_info["type"] = "datetime"
            date_cols.append(col)
        else:
            col_info["type"] = "categorical"
            categorical_cols.append(col)

        analysis["column_info"].append(col_info)

    # Suggerisci widget basati sui dati
    suggestions = []

    # KPI per valori singoli o aggregati
    for num_col in numeric_cols[:3]:  # Max 3 KPI
        suggestions.append(
            {
                "type": "kpi",
                "title": f"Totale {num_col}",
                "query_hint": f"SELECT SUM({num_col}) as total FROM table",
                "config": {"column": num_col, "aggregation": "sum"},
            }
        )

    # Bar chart per categorie vs numeri
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        suggestions.append(
            {
                "type": "bar_chart",
                "title": f"{num_col} per {cat_col}",
                "query_hint": f"SELECT {cat_col}, SUM({num_col}) FROM table GROUP BY {cat_col}",
                "config": {"x_column": cat_col, "y_column": num_col},
            }
        )

    # Pie chart per distribuzione
    if categorical_cols and numeric_cols and len(df) <= 10:
        suggestions.append(
            {
                "type": "pie_chart",
                "title": f"Distribuzione {categorical_cols[0]}",
                "config": {"label_column": categorical_cols[0], "value_column": numeric_cols[0]},
            }
        )

    # Line chart per serie temporali
    if date_cols and numeric_cols:
        suggestions.append(
            {
                "type": "line_chart",
                "title": f"Trend {numeric_cols[0]}",
                "config": {"x_column": date_cols[0], "y_column": numeric_cols[0]},
            }
        )

    # Scatter per correlazioni
    if len(numeric_cols) >= 2:
        suggestions.append(
            {
                "type": "scatter",
                "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                "config": {"x_column": numeric_cols[0], "y_column": numeric_cols[1]},
            }
        )

    # Tabella come fallback
    suggestions.append({"type": "table", "title": "Dati Completi", "config": {"columns": list(df.columns)[:10]}})

    analysis["suggested_widgets"] = suggestions
    analysis["data_profile"] = {
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
    }

    return analysis


def generate_auto_dashboard(df: pd.DataFrame, name: str = "Auto Dashboard") -> Dict[str, Any]:
    """
    Generate automatic dashboard configuration based on data.

    Returns:
        Dashboard configuration ready for rendering
    """
    analysis = analyze_dataframe(df)

    if "error" in analysis:
        return {"error": analysis["error"]}

    widgets = []
    grid_position = {"row": 0, "col": 0}

    # Aggiungi KPI in alto
    kpi_widgets = [w for w in analysis["suggested_widgets"] if w["type"] == "kpi"]
    for i, kpi in enumerate(kpi_widgets[:4]):
        widgets.append(
            {
                "id": f"widget_{len(widgets)}",
                "type": "kpi",
                "title": kpi["title"],
                "config": kpi["config"],
                "position": {"row": 0, "col": i, "width": 1, "height": 1},
            }
        )

    # Aggiungi grafici principali
    chart_widgets = [w for w in analysis["suggested_widgets"] if w["type"] in ["bar_chart", "pie_chart", "line_chart"]]
    for i, chart in enumerate(chart_widgets[:2]):
        widgets.append(
            {
                "id": f"widget_{len(widgets)}",
                "type": chart["type"],
                "title": chart["title"],
                "config": chart["config"],
                "position": {"row": 1, "col": i * 2, "width": 2, "height": 2},
            }
        )

    # Aggiungi tabella in fondo
    table_widget = next((w for w in analysis["suggested_widgets"] if w["type"] == "table"), None)
    if table_widget:
        widgets.append(
            {
                "id": f"widget_{len(widgets)}",
                "type": "table",
                "title": table_widget["title"],
                "config": table_widget["config"],
                "position": {"row": 3, "col": 0, "width": 4, "height": 2},
            }
        )

    dashboard_config = {
        "name": name,
        "created_at": datetime.utcnow().isoformat(),
        "grid": {"cols": 4, "rows": 5},
        "widgets": widgets,
        "theme": "dark",
        "auto_generated": True,
        "data_analysis": analysis,
    }

    return dashboard_config


# -----------------------------------------------------------------------------
# Dashboard Management
# -----------------------------------------------------------------------------


def save_dashboard(user_id: int, name: str, config: Dict, is_default: bool = False) -> Tuple[bool, str, Optional[int]]:
    """Save a dashboard for the user."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()

    try:
        # Se è default, rimuovi flag da altre
        if is_default:
            cursor.execute("UPDATE dashboards SET is_default = 0 WHERE user_id = ?", (user_id,))

        cursor.execute(
            """INSERT INTO dashboards (user_id, name, config, is_default) 
               VALUES (?, ?, ?, ?)""",
            (user_id, name, json.dumps(config), is_default),
        )
        dashboard_id = cursor.lastrowid
        conn.commit()
        return True, "Dashboard saved", dashboard_id
    except Exception as e:
        return False, str(e), None
    finally:
        conn.close()


def get_user_dashboards(user_id: int) -> List[Dict]:
    """Ottiene tutte le dashboard dell'utente."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, name, config, created_at, updated_at, is_default 
           FROM dashboards WHERE user_id = ? ORDER BY is_default DESC, created_at DESC""",
        (user_id,),
    )
    results = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "config": json.loads(r[2]),
            "created_at": r[3],
            "updated_at": r[4],
            "is_default": bool(r[5]),
        }
        for r in results
    ]


def get_dashboard(user_id: int, dashboard_id: int) -> Optional[Dict]:
    """Ottiene una dashboard specifica."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, name, config, created_at, updated_at, is_default 
           FROM dashboards WHERE id = ? AND user_id = ?""",
        (dashboard_id, user_id),
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    return {
        "id": result[0],
        "name": result[1],
        "config": json.loads(result[2]),
        "created_at": result[3],
        "updated_at": result[4],
        "is_default": bool(result[5]),
    }


def update_dashboard(user_id: int, dashboard_id: int, config: Dict) -> Tuple[bool, str]:
    """Aggiorna una dashboard."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        """UPDATE dashboards SET config = ?, updated_at = ? 
           WHERE id = ? AND user_id = ?""",
        (json.dumps(config), datetime.utcnow().isoformat(), dashboard_id, user_id),
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return updated, "Dashboard aggiornata" if updated else "Dashboard non trovata"


def delete_dashboard(user_id: int, dashboard_id: int) -> bool:
    """Elimina una dashboard."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dashboards WHERE id = ? AND user_id = ?", (dashboard_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ============================================================================
# TEMPLATE DASHBOARD PREDEFINITE
# ============================================================================

DASHBOARD_TEMPLATES = {
    "sales_overview": {
        "name": "Panoramica Vendite",
        "description": "Dashboard per analisi vendite con KPI e trend",
        "widgets": [
            {"type": "kpi", "title": "Fatturato Totale", "query": "SELECT SUM(total) FROM orders"},
            {"type": "kpi", "title": "Numero Ordini", "query": "SELECT COUNT(*) FROM orders"},
            {"type": "kpi", "title": "Valore Medio Ordine", "query": "SELECT AVG(total) FROM orders"},
            {
                "type": "bar_chart",
                "title": "Vendite per Regione",
                "query": "SELECT region, SUM(total) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY region",
            },
            {
                "type": "pie_chart",
                "title": "Ordini per Segmento",
                "query": "SELECT segment, COUNT(*) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY segment",
            },
            {
                "type": "line_chart",
                "title": "Trend Mensile",
                "query": "SELECT strftime('%Y-%m', order_date), SUM(total) FROM orders GROUP BY 1",
            },
        ],
    },
    "customer_analysis": {
        "name": "Analisi Clienti",
        "description": "Dashboard per analisi clientela",
        "widgets": [
            {"type": "kpi", "title": "Totale Clienti", "query": "SELECT COUNT(*) FROM customers"},
            {"type": "kpi", "title": "Clienti Attivi", "query": "SELECT COUNT(DISTINCT customer_id) FROM orders"},
            {
                "type": "bar_chart",
                "title": "Clienti per Regione",
                "query": "SELECT region, COUNT(*) FROM customers GROUP BY region",
            },
            {
                "type": "pie_chart",
                "title": "Segmentazione",
                "query": "SELECT segment, COUNT(*) FROM customers GROUP BY segment",
            },
        ],
    },
    "product_performance": {
        "name": "Performance Prodotti",
        "description": "Dashboard per analisi prodotti",
        "widgets": [
            {"type": "kpi", "title": "Totale Prodotti", "query": "SELECT COUNT(*) FROM products"},
            {
                "type": "bar_chart",
                "title": "Top 10 Prodotti",
                "query": "SELECT p.name, SUM(oi.sales) FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY 2 DESC LIMIT 10",
            },
            {
                "type": "pie_chart",
                "title": "Vendite per Categoria",
                "query": "SELECT category, SUM(sales) FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY category",
            },
        ],
    },
}


def get_dashboard_templates() -> List[Dict]:
    """Restituisce i template disponibili."""
    return [
        {"id": key, "name": template["name"], "description": template["description"], "widget_count": len(template["widgets"])}
        for key, template in DASHBOARD_TEMPLATES.items()
    ]


def create_dashboard_from_template(user_id: int, template_id: str) -> Tuple[bool, str, Optional[int]]:
    """Crea una dashboard da un template."""
    if template_id not in DASHBOARD_TEMPLATES:
        return False, "Template non trovato", None

    template = DASHBOARD_TEMPLATES[template_id]

    config = {
        "name": template["name"],
        "created_at": datetime.utcnow().isoformat(),
        "grid": {"cols": 4, "rows": 5},
        "widgets": [],
        "theme": "dark",
        "from_template": template_id,
    }

    # Posiziona widget automaticamente
    for i, widget in enumerate(template["widgets"]):
        row = i // 2
        col = (i % 2) * 2
        width = 2 if widget["type"] != "kpi" else 1
        height = 2 if widget["type"] != "kpi" else 1

        config["widgets"].append(
            {
                "id": f"widget_{i}",
                "type": widget["type"],
                "title": widget["title"],
                "query": widget.get("query"),
                "position": {"row": row, "col": col, "width": width, "height": height},
            }
        )

    return save_dashboard(user_id, template["name"], config)


# ============================================================================
# DASHBOARD MANAGER CLASS (Wrapper per main.py)
# ============================================================================


class DashboardManager:
    """
    Classe wrapper per le funzioni dashboard.
    Fornisce un'interfaccia unificata per main.py.
    """

    def analyze_data(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Analizza i dati e restituisce statistiche.

        Args:
            data: Lista di dizionari (record)

        Returns:
            Analisi dei dati
        """
        try:
            df = pd.DataFrame(data)
            return analyze_dataframe(df)
        except Exception as e:
            return {"error": str(e)}

    def suggest_visualizations(self, data: List[Dict], analysis: Dict = None) -> List[Dict]:
        """
        Suggerisce visualizzazioni appropriate per i dati.

        Args:
            data: Lista di dizionari
            analysis: Analisi precedente (opzionale)

        Returns:
            Lista di suggerimenti widget
        """
        try:
            df = pd.DataFrame(data)
            if analysis is None:
                analysis = analyze_dataframe(df)

            return analysis.get("suggested_widgets", [])
        except Exception as e:
            return []

    def create_dashboard(self, data: List[Dict], title: str = "Dashboard") -> Dict:
        """
        Crea una dashboard automatica dai dati.

        Args:
            data: Lista di dizionari
            title: Titolo della dashboard

        Returns:
            Configurazione dashboard
        """
        try:
            df = pd.DataFrame(data)
            dashboard = generate_auto_dashboard(df, title)

            # Aggiungi statistiche
            dashboard["stats"] = {"total_rows": len(df), "total_columns": len(df.columns), "column_names": list(df.columns)}

            return DashboardLayout(dashboard)
        except Exception as e:
            return DashboardLayout({"error": str(e), "widgets": [], "title": title})

    def save_dashboard(self, dashboard_id: str, layout: Dict) -> bool:
        """Salva una dashboard."""
        # Per utenti anonimi, salviamo in memoria/session
        # In futuro con auth, salveremo nel DB
        return True

    def load_dashboard(self, dashboard_id: str) -> Optional[Dict]:
        """Carica una dashboard salvata."""
        # Per ora restituisce None (non implementato per utenti anonimi)
        return None


class DashboardLayout:
    """Wrapper per layout dashboard."""

    def __init__(self, config: Dict):
        self.config = config

    def to_dict(self) -> Dict:
        """Converte in dizionario."""
        return self.config


# Istanza singleton
dashboard_manager = DashboardManager()
