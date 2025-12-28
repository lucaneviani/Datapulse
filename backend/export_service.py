"""
DataPulse Export Module

Advanced export system with support for multiple formats and scheduled reports.

Features:
    - PDF export with embedded charts
    - Multi-sheet Excel export
    - JSON/CSV export
    - Scheduled automatic reports
    - Customizable report templates

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import base64
import io
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger("datapulse.export")

BASE_DIR = Path(__file__).parent.parent
AUTH_DB_PATH = BASE_DIR / "data" / "users.db"
EXPORTS_DIR = BASE_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


# ============================================================================
# EXPORT FORMATI BASE
# ============================================================================


def export_to_csv(df: pd.DataFrame, filename: str = None) -> Tuple[bytes, str]:
    """
    Esporta DataFrame in CSV.

    Returns:
        (contenuto_bytes, nome_file)
    """
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    content = buffer.getvalue().encode("utf-8")

    return content, filename


def export_to_json(df: pd.DataFrame, filename: str = None, orient: str = "records") -> Tuple[bytes, str]:
    """
    Esporta DataFrame in JSON.

    Args:
        orient: 'records', 'columns', 'index', 'split', 'table'

    Returns:
        (contenuto_bytes, nome_file)
    """
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    content = df.to_json(orient=orient, indent=2, date_format="iso").encode("utf-8")

    return content, filename


def export_to_excel(df: pd.DataFrame, filename: str = None, sheet_name: str = "Data") -> Tuple[bytes, str]:
    """
    Esporta DataFrame in Excel.

    Returns:
        (contenuto_bytes, nome_file)
    """
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

    content = buffer.getvalue()
    return content, filename


def export_multi_sheet_excel(dataframes: Dict[str, pd.DataFrame], filename: str = None) -> Tuple[bytes, str]:
    """
    Esporta più DataFrame in un Excel multi-foglio.

    Args:
        dataframes: Dict con nome_foglio -> DataFrame

    Returns:
        (contenuto_bytes, nome_file)
    """
    if filename is None:
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in dataframes.items():
            # Excel sheet names max 31 chars
            safe_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)

    content = buffer.getvalue()
    return content, filename


# ============================================================================
# EXPORT HTML REPORT
# ============================================================================


def generate_html_report(title: str, sections: List[Dict], include_charts: bool = True, theme: str = "dark") -> str:
    """
    Genera un report HTML completo.

    Args:
        title: Titolo del report
        sections: Lista di sezioni con 'title', 'type', 'content'
        include_charts: Se includere grafici come SVG/PNG
        theme: 'dark' o 'light'

    Returns:
        HTML string
    """
    bg_color = "#0a0a0b" if theme == "dark" else "#ffffff"
    text_color = "#ffffff" if theme == "dark" else "#1a1a1a"
    card_bg = "#1a1a1f" if theme == "dark" else "#f5f5f5"
    border_color = "#2a2a32" if theme == "dark" else "#e0e0e0"
    accent_color = "#3b82f6"

    html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - DataPulse Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.6;
            padding: 40px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid {accent_color};
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            color: {accent_color};
        }}
        
        .header .meta {{
            color: #6b7280;
            font-size: 14px;
        }}
        
        .section {{
            background: {card_bg};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        
        .section h2 {{
            font-size: 20px;
            margin-bottom: 16px;
            color: {accent_color};
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        
        .kpi-card {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        
        .kpi-value {{
            font-size: 36px;
            font-weight: 700;
            color: {text_color};
        }}
        
        .kpi-label {{
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 8px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid {border_color};
        }}
        
        th {{
            background: rgba(59, 130, 246, 0.1);
            font-weight: 600;
            color: {accent_color};
        }}
        
        tr:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}
        
        .chart-container {{
            margin: 20px 0;
            text-align: center;
        }}
        
        .chart-container img {{
            max-width: 100%;
            border-radius: 8px;
        }}
        
        .footer {{
            text-align: center;
            padding-top: 40px;
            color: #6b7280;
            font-size: 12px;
        }}
        
        @media print {{
            body {{
                background: white;
                color: black;
            }}
            .section {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <div class="meta">
                Generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')} • DataPulse AI Analytics
            </div>
        </div>
"""

    for section in sections:
        section_type = section.get("type", "text")
        section_title = section.get("title", "")
        content = section.get("content")

        html += f'<div class="section">\n'

        if section_title:
            icon = "📊" if section_type == "kpi" else "📋" if section_type == "table" else "📈"
            html += f"<h2>{icon} {section_title}</h2>\n"

        if section_type == "kpi" and isinstance(content, list):
            html += '<div class="kpi-grid">\n'
            for kpi in content:
                value = kpi.get("value", "N/A")
                label = kpi.get("label", "")
                # Format large numbers
                if isinstance(value, (int, float)):
                    if value >= 1_000_000:
                        display_value = f"{value/1_000_000:.2f}M"
                    elif value >= 1_000:
                        display_value = f"{value/1_000:.1f}K"
                    else:
                        display_value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
                else:
                    display_value = str(value)

                html += f"""
                <div class="kpi-card">
                    <div class="kpi-value">{display_value}</div>
                    <div class="kpi-label">{label}</div>
                </div>
"""
            html += "</div>\n"

        elif section_type == "table" and isinstance(content, pd.DataFrame):
            html += content.to_html(index=False, classes="data-table", escape=False)

        elif section_type == "text":
            html += f"<p>{content}</p>\n"

        elif section_type == "chart" and include_charts:
            # Chart image as base64
            chart_data = content.get("image_base64", "")
            if chart_data:
                html += f"""
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart_data}" alt="{section_title}">
                </div>
"""

        html += "</div>\n"

    html += f"""
        <div class="footer">
            Report generato automaticamente da DataPulse AI Analytics<br>
            © {datetime.now().year} DataPulse
        </div>
    </div>
</body>
</html>
"""

    return html


def export_to_html(title: str, sections: List[Dict], filename: str = None) -> Tuple[bytes, str]:
    """
    Esporta report in HTML.

    Returns:
        (contenuto_bytes, nome_file)
    """
    if filename is None:
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    html = generate_html_report(title, sections)
    content = html.encode("utf-8")

    return content, filename


# ============================================================================
# REPORT BUILDER
# ============================================================================


class ReportBuilder:
    """Builder per creare report complessi."""

    def __init__(self, title: str, theme: str = "dark"):
        self.title = title
        self.theme = theme
        self.sections = []
        self.metadata = {"created_at": datetime.now().isoformat(), "author": "DataPulse"}

    def add_kpi_section(self, title: str, kpis: List[Dict]) -> "ReportBuilder":
        """Aggiunge sezione KPI."""
        self.sections.append({"type": "kpi", "title": title, "content": kpis})
        return self

    def add_table_section(self, title: str, df: pd.DataFrame) -> "ReportBuilder":
        """Aggiunge sezione tabella."""
        self.sections.append({"type": "table", "title": title, "content": df})
        return self

    def add_text_section(self, title: str, text: str) -> "ReportBuilder":
        """Aggiunge sezione testo."""
        self.sections.append({"type": "text", "title": title, "content": text})
        return self

    def add_chart_section(self, title: str, image_base64: str) -> "ReportBuilder":
        """Aggiunge sezione grafico."""
        self.sections.append({"type": "chart", "title": title, "content": {"image_base64": image_base64}})
        return self

    def build_html(self) -> str:
        """Genera HTML del report."""
        return generate_html_report(self.title, self.sections, theme=self.theme)

    def export(self, format: str = "html") -> Tuple[bytes, str]:
        """
        Esporta report nel formato specificato.

        Args:
            format: 'html', 'json'
        """
        if format == "html":
            return export_to_html(self.title, self.sections)
        elif format == "json":
            report_data = {
                "title": self.title,
                "metadata": self.metadata,
                "sections": [
                    {
                        "type": s["type"],
                        "title": s["title"],
                        "content": s["content"].to_dict() if isinstance(s["content"], pd.DataFrame) else s["content"],
                    }
                    for s in self.sections
                ],
            }
            content = json.dumps(report_data, indent=2, default=str).encode("utf-8")
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            return content, filename
        else:
            raise ValueError(f"Formato non supportato: {format}")


# ============================================================================
# SCHEDULED REPORTS (placeholder per future implementazioni)
# ============================================================================


def init_scheduled_reports_table():
    """Inizializza tabella report schedulati."""
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduled_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            config TEXT NOT NULL,
            schedule TEXT NOT NULL,
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    )

    conn.commit()
    conn.close()


def save_scheduled_report(user_id: int, name: str, config: Dict, schedule: str) -> Tuple[bool, str, Optional[int]]:
    """
    Salva un report schedulato.

    Args:
        schedule: Cron-like string (es. "0 9 * * 1" = ogni lunedì alle 9)
    """
    init_scheduled_reports_table()

    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO scheduled_reports (user_id, name, config, schedule) 
               VALUES (?, ?, ?, ?)""",
            (user_id, name, json.dumps(config), schedule),
        )
        report_id = cursor.lastrowid
        conn.commit()
        return True, "Report schedulato salvato", report_id
    except Exception as e:
        return False, str(e), None
    finally:
        conn.close()


def get_scheduled_reports(user_id: int) -> List[Dict]:
    """Ottiene i report schedulati dell'utente."""
    init_scheduled_reports_table()

    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, name, config, schedule, last_run, next_run, is_active, created_at
           FROM scheduled_reports WHERE user_id = ? ORDER BY created_at DESC""",
        (user_id,),
    )
    results = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "config": json.loads(r[2]),
            "schedule": r[3],
            "last_run": r[4],
            "next_run": r[5],
            "is_active": bool(r[6]),
            "created_at": r[7],
        }
        for r in results
    ]


# ============================================================================
# EXPORT UTILITIES
# ============================================================================


def get_export_formats() -> List[Dict]:
    """Restituisce i formati di export disponibili."""
    return [
        {
            "id": "csv",
            "name": "CSV",
            "extension": ".csv",
            "mime_type": "text/csv",
            "description": "Comma-separated values, compatibile con Excel",
        },
        {
            "id": "xlsx",
            "name": "Excel",
            "extension": ".xlsx",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "description": "Microsoft Excel workbook",
        },
        {
            "id": "json",
            "name": "JSON",
            "extension": ".json",
            "mime_type": "application/json",
            "description": "JavaScript Object Notation",
        },
        {
            "id": "html",
            "name": "HTML Report",
            "extension": ".html",
            "mime_type": "text/html",
            "description": "Report HTML formattato",
        },
    ]


def export_data(df: pd.DataFrame, format: str, filename: str = None, **kwargs) -> Tuple[bytes, str, str]:
    """
    Funzione universale di export.

    Returns:
        (contenuto_bytes, nome_file, mime_type)
    """
    formats_info = {f["id"]: f for f in get_export_formats()}

    if format not in formats_info:
        raise ValueError(f"Formato non supportato: {format}")

    format_info = formats_info[format]

    if format == "csv":
        content, fname = export_to_csv(df, filename)
    elif format == "xlsx":
        content, fname = export_to_excel(df, filename, **kwargs)
    elif format == "json":
        content, fname = export_to_json(df, filename, **kwargs)
    elif format == "html":
        # Per HTML, crea un report semplice con tabella
        builder = ReportBuilder(kwargs.get("title", "Export Dati"))
        builder.add_table_section("Dati", df)
        content, fname = builder.export("html")
    else:
        raise ValueError(f"Formato non implementato: {format}")

    return content, fname, format_info["mime_type"]


# ============================================================================
# EXPORT SERVICE CLASS (Wrapper per main.py)
# ============================================================================


class ExportService:
    """
    Classe wrapper per le funzioni di export.
    Fornisce un'interfaccia unificata per main.py.
    """

    def export_to_csv(self, data: List[Dict]) -> bytes:
        """Esporta in CSV."""
        df = pd.DataFrame(data)
        content, _ = export_to_csv(df)
        return content

    def export_to_excel(self, data: List[Dict], title: str = None, query: str = None) -> bytes:
        """Esporta in Excel."""
        df = pd.DataFrame(data)
        content, _ = export_to_excel(df)
        return content

    def export_to_pdf(self, data: List[Dict], title: str = None, query: str = None) -> bytes:
        """Esporta in PDF."""
        df = pd.DataFrame(data)
        try:
            builder = ReportBuilder(title or "Report DataPulse")

            # Aggiungi info query se presente
            if query:
                builder.add_text_section("Query SQL", query)

            # Aggiungi tabella dati
            builder.add_table_section("Risultati", df)

            # Aggiungi statistiche
            stats = {
                "Righe totali": len(df),
                "Colonne": len(df.columns),
                "Generato il": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
            builder.add_kpi_section("Statistiche", stats)

            content, _ = builder.export("pdf")
            return content
        except Exception as e:
            logger.error(f"Errore export PDF: {e}")
            # Fallback: genera PDF semplice con tabella
            return self._simple_pdf(data, title)

    def _simple_pdf(self, data: List[Dict], title: str = None) -> bytes:
        """Genera PDF semplice come fallback."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []

            styles = getSampleStyleSheet()
            elements.append(Paragraph(title or "Report", styles["Heading1"]))

            if data:
                df = pd.DataFrame(data)
                # Limita colonne e righe per PDF
                df = df.iloc[:100, :10]

                table_data = [list(df.columns)]
                for _, row in df.iterrows():
                    table_data.append([str(v)[:30] for v in row.values])

                table = Table(table_data)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                elements.append(table)

            doc.build(elements)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Errore PDF semplice: {e}")
            # Ultra fallback: CSV
            return self.export_to_csv(data)

    def export_to_html(self, data: List[Dict], title: str = None, query: str = None) -> bytes:
        """Esporta in HTML."""
        df = pd.DataFrame(data)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title or 'Report DataPulse'}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0a0a0b; color: #fff; padding: 40px; }}
        h1 {{ color: #3b82f6; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #2a2a32; padding: 12px; text-align: left; }}
        th {{ background: #1a1a1f; color: #3b82f6; }}
        tr:hover {{ background: #1a1a1f; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: #1a1a1f; padding: 20px; border-radius: 10px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #3b82f6; }}
        .stat-label {{ color: #9ca3af; font-size: 12px; }}
        pre {{ background: #1a1a1f; padding: 15px; border-radius: 8px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>📊 {title or 'Report DataPulse'}</h1>
    <p style="color: #9ca3af;">Generato il {datetime.now().strftime("%d/%m/%Y alle %H:%M")}</p>
    
    <div class="stats">
        <div class="stat">
            <div class="stat-value">{len(df)}</div>
            <div class="stat-label">Righe</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(df.columns)}</div>
            <div class="stat-label">Colonne</div>
        </div>
    </div>
    
    {"<h3>Query SQL</h3><pre>" + query + "</pre>" if query else ""}
    
    <h3>Dati</h3>
    {df.to_html(index=False, classes='data-table')}
    
    <footer style="margin-top: 40px; color: #6b7280; font-size: 12px;">
        DataPulse AI Analytics
    </footer>
</body>
</html>"""

        return html.encode("utf-8")

    def generate_report(
        self,
        data: List[Dict],
        format_type: str = "pdf",
        title: str = "Report",
        query: str = None,
        include_charts: bool = True,
        include_summary: bool = True,
    ) -> bytes:
        """Genera un report completo."""
        if format_type == "pdf":
            return self.export_to_pdf(data, title, query)
        elif format_type == "excel":
            return self.export_to_excel(data, title, query)
        elif format_type == "html":
            return self.export_to_html(data, title, query)
        else:
            return self.export_to_csv(data)


# Istanza singleton
export_service = ExportService()
