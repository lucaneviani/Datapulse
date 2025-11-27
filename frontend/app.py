"""
DataPulse - AI-Powered Business Intelligence Frontend
======================================================
Interfaccia Streamlit avanzata per interrogare dati aziendali
usando linguaggio naturale e visualizzare risultati con grafici dinamici.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# ============================================================================
# CONFIGURAZIONE
# ============================================================================

# URL backend da variabile d'ambiente (fallback a localhost per sviluppo)
BACKEND_URL = os.getenv("DATAPULSE_BACKEND_URL", "http://127.0.0.1:8000/api/analyze")
REQUEST_TIMEOUT = 30  # Timeout in secondi per le richieste

# Configurazione pagina Streamlit
st.set_page_config(
    page_title="DataPulse - AI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PERSONALIZZATO PER TEMA SCURO E UI MIGLIORATA
# ============================================================================

st.markdown("""
<style>
    /* Stile generale */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    
    /* Card per risultati */
    .result-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #333;
    }
    
    /* Stile per SQL code */
    .sql-box {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Fira Code', monospace;
    }
    
    /* Bottoni stilizzati */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #1a1a2e;
    }
    
    /* Metriche stilizzate */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INIZIALIZZAZIONE SESSION STATE
# ============================================================================

def init_session_state():
    """Inizializza le variabili di sessione per mantenere stato tra refresh."""
    if "query_history" not in st.session_state:
        st.session_state.query_history = []  # Lista di query eseguite
    if "current_results" not in st.session_state:
        st.session_state.current_results = None  # Risultati correnti
    if "current_sql" not in st.session_state:
        st.session_state.current_sql = None  # SQL corrente
    if "current_df" not in st.session_state:
        st.session_state.current_df = None  # DataFrame corrente

init_session_state()

# ============================================================================
# FUNZIONI HELPER
# ============================================================================

def validate_question(question: str) -> tuple[bool, str]:
    """
    Valida l'input della domanda.
    Returns: (is_valid, error_message)
    """
    if not question or not question.strip():
        return False, "⚠️ Inserisci una domanda valida."
    if len(question.strip()) < 5:
        return False, "⚠️ La domanda è troppo corta. Prova ad essere più specifico."
    if len(question) > 500:
        return False, "⚠️ La domanda è troppo lunga. Massimo 500 caratteri."
    return True, ""


def call_backend(question: str) -> Dict[str, Any]:
    """
    Effettua la chiamata al backend FastAPI.
    Returns: Dizionario con risultati o errore.
    """
    payload = {"question": question}
    try:
        response = requests.post(
            BACKEND_URL, 
            json=payload, 
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False, 
                "error": f"Errore {response.status_code}: {response.text}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False, 
            "error": "⏱️ Timeout: Il server ha impiegato troppo tempo a rispondere."
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False, 
            "error": "🔌 Impossibile connettersi al backend. Assicurati che il server sia avviato."
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"❌ Errore di rete: {str(e)}"}


def detect_chart_type(df: pd.DataFrame, sql: str) -> str:
    """
    Rileva automaticamente il tipo di grafico migliore basandosi sui dati e SQL.
    Returns: 'bar', 'pie', 'line', 'table', 'metric'
    """
    if df is None or df.empty:
        return "table"
    
    sql_lower = sql.lower()
    num_rows = len(df)
    num_cols = len(df.columns)
    
    # Se è un singolo valore (COUNT, SUM singolo), mostra come metrica
    if num_rows == 1 and num_cols == 1:
        return "metric"
    
    # Se ha colonne numeriche e categoriche, determina grafico
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Aggregazioni con GROUP BY -> bar chart
    if ("group by" in sql_lower or "sum" in sql_lower or "count" in sql_lower) and len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        if num_rows <= 10:
            return "pie"
        return "bar"
    
    # Time series (date nel nome colonna)
    date_cols = [c for c in df.columns if any(d in c.lower() for d in ['date', 'month', 'year', 'time'])]
    if date_cols and len(numeric_cols) >= 1:
        return "line"
    
    # Default: tabella
    return "table"


def create_visualization(df: pd.DataFrame, chart_type: str, sql: str):
    """
    Crea la visualizzazione appropriata basata sul tipo rilevato.
    """
    if df is None or df.empty:
        st.info("📭 Nessun dato da visualizzare.")
        return
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if chart_type == "metric":
        # Singolo valore grande
        value = df.iloc[0, 0]
        col_name = df.columns[0]
        st.metric(label=col_name, value=f"{value:,}" if isinstance(value, (int, float)) else value)
        
    elif chart_type == "bar":
        if categorical_cols and numeric_cols:
            fig = px.bar(
                df, 
                x=categorical_cols[0], 
                y=numeric_cols[0],
                title=f"📊 {numeric_cols[0]} per {categorical_cols[0]}",
                color=categorical_cols[0],
                template="plotly_dark"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
            
    elif chart_type == "pie":
        if categorical_cols and numeric_cols:
            fig = px.pie(
                df, 
                names=categorical_cols[0], 
                values=numeric_cols[0],
                title=f"🥧 Distribuzione {numeric_cols[0]}",
                template="plotly_dark",
                hole=0.4  # Donut chart
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
            
    elif chart_type == "line":
        date_cols = [c for c in df.columns if any(d in c.lower() for d in ['date', 'month', 'year', 'time'])]
        if date_cols and numeric_cols:
            fig = px.line(
                df, 
                x=date_cols[0], 
                y=numeric_cols[0],
                title=f"📈 Trend {numeric_cols[0]}",
                template="plotly_dark",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        # Default: tabella interattiva
        st.dataframe(df, use_container_width=True)


def add_to_history(question: str, sql: str, success: bool):
    """Aggiunge una query alla cronologia."""
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "question": question[:50] + "..." if len(question) > 50 else question,
        "sql": sql,
        "success": success
    }
    st.session_state.query_history.insert(0, entry)
    # Mantieni solo le ultime 10 query
    st.session_state.query_history = st.session_state.query_history[:10]


def get_example_questions() -> List[str]:
    """Restituisce domande di esempio per guidare l'utente."""
    return [
        "Quanti clienti ci sono in totale?",
        "Qual è il totale delle vendite per regione?",
        "Quali sono i 5 prodotti più venduti?",
        "Quanti ordini sono stati fatti nel 2023?",
        "Qual è la media delle vendite per categoria?",
        "Quali clienti hanno speso più di 1000€?",
        "Mostra le vendite mensili dell'ultimo anno",
        "Quali prodotti hanno prezzo superiore a 100?"
    ]

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## 🎛️ Pannello di Controllo")
    st.markdown("---")
    
    # Sezione: Domande di esempio
    st.markdown("### 💡 Domande di Esempio")
    example_questions = get_example_questions()
    selected_example = st.selectbox(
        "Seleziona un esempio:",
        ["-- Scegli --"] + example_questions,
        key="example_selector"
    )
    
    st.markdown("---")
    
    # Sezione: Cronologia Query
    st.markdown("### 📜 Cronologia Query")
    if st.session_state.query_history:
        for i, entry in enumerate(st.session_state.query_history[:5]):
            status = "✅" if entry["success"] else "❌"
            with st.expander(f"{status} {entry['timestamp']} - {entry['question'][:25]}..."):
                st.code(entry["sql"], language="sql")
    else:
        st.info("Nessuna query eseguita.")
    
    if st.button("🗑️ Cancella Cronologia"):
        st.session_state.query_history = []
        st.rerun()
    
    st.markdown("---")
    
    # Sezione: Esporta Dati
    st.markdown("### 💾 Esporta Dati")
    if st.session_state.current_df is not None and not st.session_state.current_df.empty:
        csv = st.session_state.current_df.to_csv(index=False)
        st.download_button(
            label="📥 Scarica CSV",
            data=csv,
            file_name=f"datapulse_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Esegui una query per abilitare l'export.")
    
    st.markdown("---")
    
    # Info Backend
    st.markdown("### ⚙️ Configurazione")
    st.caption(f"Backend URL: `{BACKEND_URL}`")
    st.caption(f"Timeout: {REQUEST_TIMEOUT}s")

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header principale
st.markdown('<h1 class="main-header">📊 DataPulse</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Interroga i tuoi dati aziendali con il linguaggio naturale</p>', unsafe_allow_html=True)

# Area input principale
col1, col2 = st.columns([5, 1])

with col1:
    # Se è stata selezionata una domanda di esempio, usala
    default_question = selected_example if selected_example != "-- Scegli --" else ""
    question = st.text_input(
        "🔍 Fai una domanda sui tuoi dati:",
        value=default_question,
        placeholder="Es: Quanti clienti ci sono per regione?",
        key="main_question_input"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_clicked = st.button("🚀 Analizza", use_container_width=True)

# Elaborazione della query
if analyze_clicked:
    # Validazione input
    is_valid, error_msg = validate_question(question)
    
    if not is_valid:
        st.warning(error_msg)
    else:
        # Chiamata al backend con spinner
        with st.spinner("🤖 L'AI sta analizzando la tua domanda..."):
            result = call_backend(question)
        
        if result["success"]:
            data = result["data"]
            generated_sql = data.get("generated_sql", "N/A")
            query_results = data.get("data", [])
            
            # Salva in session state
            st.session_state.current_sql = generated_sql
            st.session_state.current_df = pd.DataFrame(query_results) if query_results else pd.DataFrame()
            st.session_state.current_results = query_results
            
            # Aggiungi alla cronologia
            add_to_history(question, generated_sql, True)
            
            st.success("✅ Query eseguita con successo!")
            
        else:
            st.error(result["error"])
            add_to_history(question, "ERRORE", False)
            
            # Suggerimenti per l'utente
            st.markdown("### 💡 Suggerimenti:")
            st.markdown("""
            - Assicurati che il backend sia in esecuzione (`uvicorn backend.main:app --reload`)
            - Prova con una domanda più semplice
            - Verifica che le tabelle esistano nel database (customers, products, orders, order_items)
            """)

# ============================================================================
# SEZIONE RISULTATI
# ============================================================================

if st.session_state.current_sql:
    st.markdown("---")
    
    # Due colonne: SQL e Visualizzazione
    col_sql, col_viz = st.columns([1, 2])
    
    with col_sql:
        st.markdown("### 🔧 SQL Generato")
        st.code(st.session_state.current_sql, language="sql")
        
        # Info sul DataFrame
        if st.session_state.current_df is not None and not st.session_state.current_df.empty:
            df = st.session_state.current_df
            st.markdown("#### 📋 Info Dataset")
            st.caption(f"Righe: {len(df)} | Colonne: {len(df.columns)}")
            st.caption(f"Colonne: {', '.join(df.columns.tolist())}")
    
    with col_viz:
        st.markdown("### 📈 Risultati")
        
        if st.session_state.current_df is not None and not st.session_state.current_df.empty:
            df = st.session_state.current_df
            
            # Rileva tipo di grafico automaticamente
            chart_type = detect_chart_type(df, st.session_state.current_sql)
            
            # Toggle per scegliere visualizzazione
            viz_options = ["Auto", "Tabella", "Grafico a Barre", "Grafico a Torta", "Linea"]
            selected_viz = st.radio(
                "Tipo visualizzazione:",
                viz_options,
                horizontal=True,
                key="viz_selector"
            )
            
            # Mappa selezione a tipo
            viz_map = {
                "Auto": chart_type,
                "Tabella": "table",
                "Grafico a Barre": "bar",
                "Grafico a Torta": "pie",
                "Linea": "line"
            }
            
            final_chart_type = viz_map.get(selected_viz, "table")
            
            # Crea visualizzazione
            create_visualization(df, final_chart_type, st.session_state.current_sql)
            
        else:
            st.info("📭 Nessun dato restituito dalla query.")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85rem;">
    <p>📊 <strong>DataPulse</strong> - AI-Powered Business Intelligence</p>
    <p>Backend: FastAPI + SQLite | AI: Google Gemini | Frontend: Streamlit + Plotly</p>
</div>
""", unsafe_allow_html=True)