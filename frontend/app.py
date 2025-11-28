"""
DataPulse Frontend - Streamlit Application
==========================================
Professional dark-themed UI for AI-powered data analytics.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
from datetime import datetime

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="DataPulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CONSTANTS
# =============================================================================

BACKEND_URL = "http://127.0.0.1:8000"
API_ENDPOINT = f"{BACKEND_URL}/api/analyze"

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables */
    :root {
        --bg-primary: #0a0a0b;
        --bg-secondary: #141417;
        --bg-card: #1a1a1f;
        --bg-hover: #222228;
        --border-color: #2a2a32;
        --text-primary: #ffffff;
        --text-secondary: #9ca3af;
        --text-muted: #6b7280;
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-yellow: #f59e0b;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--bg-primary);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    
    /* Text Input */
    .stTextInput > div > div > input {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--text-muted) !important;
    }
    
    /* Primary Button */
    .stButton > button[kind="primary"],
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }
    
    .stDownloadButton > button:hover {
        background: var(--bg-hover) !important;
        border-color: var(--text-muted) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bg-card);
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: var(--text-secondary) !important;
        padding: 8px 16px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--bg-hover) !important;
        color: var(--text-primary) !important;
    }
    
    /* Dataframe */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Code block */
    .stCodeBlock {
        border-radius: 10px;
    }
    
    pre {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--bg-card) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    /* Select box */
    .stSelectbox > div > div {
        background-color: var(--bg-card) !important;
        border-color: var(--border-color) !important;
    }
    
    /* Custom card class */
    .custom-card {
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    /* Metric display */
    .metric-container {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 32px;
        text-align: center;
    }
    
    .metric-label {
        font-size: 14px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 48px;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    /* Status badges */
    .status-success {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
    .status-error {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
    /* History items */
    .history-item {
        background-color: rgba(255,255,255,0.02);
        border-left: 3px solid var(--border-color);
        padding: 10px 12px;
        margin-bottom: 8px;
        border-radius: 0 6px 6px 0;
        transition: background-color 0.2s;
    }
    
    .history-item:hover {
        background-color: rgba(255,255,255,0.05);
    }
    
    .history-item.success {
        border-left-color: var(--accent-green);
    }
    
    .history-item.error {
        border-left-color: var(--accent-red);
    }
    
    .history-time {
        font-size: 11px;
        color: var(--text-muted);
    }
    
    .history-text {
        font-size: 13px;
        color: var(--text-secondary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_sql" not in st.session_state:
    st.session_state.last_sql = None
if "last_df" not in st.session_state:
    st.session_state.last_df = None
if "query_time" not in st.session_state:
    st.session_state.query_time = None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_backend_health():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False


def send_query(question: str) -> dict:
    """Send query to backend API."""
    try:
        response = requests.post(
            API_ENDPOINT,
            json={"question": question},
            timeout=30
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Impossibile connettersi al backend. Verifica che sia in esecuzione."}
    except requests.exceptions.Timeout:
        return {"error": "Timeout: il server non risponde."}
    except Exception as e:
        return {"error": f"Errore: {str(e)}"}


def add_to_history(question: str, success: bool):
    """Add query to history."""
    entry = {
        "time": datetime.now().strftime("%H:%M"),
        "question": question[:50] + "..." if len(question) > 50 else question,
        "success": success
    }
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:10]


def detect_chart_type(df: pd.DataFrame) -> str:
    """Auto-detect best chart type for data."""
    if df is None or df.empty:
        return "table"
    
    rows, cols = df.shape
    
    if rows == 1 and cols == 1:
        return "metric"
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if text_cols and numeric_cols:
        if rows <= 8:
            return "pie"
        elif rows <= 20:
            return "bar"
    
    if len(numeric_cols) >= 2:
        return "scatter"
    
    return "table"


def create_chart(df: pd.DataFrame, chart_type: str):
    """Create Plotly chart."""
    if df is None or df.empty:
        st.info("📊 Nessun dato disponibile")
        return
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Chart colors
    colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4']
    
    # Common layout
    layout = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#9ca3af', size=12),
        margin=dict(t=40, b=40, l=40, r=20),
        xaxis=dict(gridcolor='#2a2a32', linecolor='#2a2a32', tickfont=dict(color='#9ca3af')),
        yaxis=dict(gridcolor='#2a2a32', linecolor='#2a2a32', tickfont=dict(color='#9ca3af')),
        legend=dict(bgcolor='rgba(26,26,31,0.9)', bordercolor='#2a2a32', font=dict(color='#ffffff'))
    )
    
    if chart_type == "metric":
        value = df.iloc[0, 0]
        label = df.columns[0]
        
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
        
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{display_value}</div>
            </div>
        """, unsafe_allow_html=True)
        
    elif chart_type == "bar" and text_cols and numeric_cols:
        fig = go.Figure(go.Bar(
            x=df[text_cols[0]],
            y=df[numeric_cols[0]],
            marker=dict(color=colors[:len(df)]),
            text=df[numeric_cols[0]].apply(lambda x: f'{x:,.0f}'),
            textposition='outside',
            textfont=dict(color='#9ca3af', size=11)
        ))
        fig.update_layout(**layout, height=400, bargap=0.3, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    elif chart_type == "pie" and text_cols and numeric_cols:
        fig = go.Figure(go.Pie(
            labels=df[text_cols[0]],
            values=df[numeric_cols[0]],
            hole=0.6,
            marker=dict(colors=colors[:len(df)], line=dict(color='#0a0a0b', width=2)),
            textinfo='percent',
            textposition='outside',
            textfont=dict(color='#9ca3af', size=12)
        ))
        
        total = df[numeric_cols[0]].sum()
        total_str = f"{total:,.0f}"
        
        fig.update_layout(
            **layout, 
            height=400,
            annotations=[dict(text=f"<b>{total_str}</b>", x=0.5, y=0.5, font=dict(size=20, color='#ffffff'), showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    elif chart_type == "line" and numeric_cols:
        x_col = df.columns[0]
        fig = go.Figure(go.Scatter(
            x=df[x_col],
            y=df[numeric_cols[0]],
            mode='lines+markers',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='#3b82f6', line=dict(color='#0a0a0b', width=2)),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        fig.update_layout(**layout, height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    elif chart_type == "scatter" and len(numeric_cols) >= 2:
        fig = go.Figure(go.Scatter(
            x=df[numeric_cols[0]],
            y=df[numeric_cols[1]],
            mode='markers',
            marker=dict(size=10, color='#3b82f6', line=dict(color='#0a0a0b', width=1))
        ))
        fig.update_layout(**layout, height=400, xaxis_title=numeric_cols[0], yaxis_title=numeric_cols[1])
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    else:
        st.dataframe(df, use_container_width=True, height=400)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    # Logo & Brand
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; padding: 16px 0; border-bottom: 1px solid #2a2a32; margin-bottom: 24px;">
            <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px;">⚡</div>
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #ffffff;">DataPulse</div>
                <div style="font-size: 12px; color: #6b7280;">AI Analytics</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # System Status
    is_online = check_backend_health()
    status_html = """
        <div class="status-success">
            <span>●</span> Sistema Online
        </div>
    """ if is_online else """
        <div class="status-error">
            <span>●</span> Backend Offline
        </div>
    """
    st.markdown(status_html, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # History Section
    st.markdown("#### 📋 Cronologia")
    
    if st.session_state.history:
        for item in st.session_state.history[:6]:
            status_class = "success" if item["success"] else "error"
            st.markdown(f"""
                <div class="history-item {status_class}">
                    <div class="history-time">{item["time"]}</div>
                    <div class="history-text">{item["question"]}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Pulisci cronologia", use_container_width=True):
            st.session_state.history = []
            st.session_state.last_result = None
            st.session_state.last_sql = None
            st.session_state.last_df = None
            st.rerun()
    else:
        st.markdown("""
            <div style="text-align: center; padding: 24px; color: #6b7280;">
                <div style="font-size: 32px; margin-bottom: 8px; opacity: 0.5;">📋</div>
                <div>Nessuna query eseguita</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Export Section
    st.markdown("#### 📥 Esporta")
    
    if st.session_state.last_df is not None and not st.session_state.last_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            csv = st.session_state.last_df.to_csv(index=False)
            st.download_button("CSV", csv, "export.csv", "text/csv", use_container_width=True)
        with col2:
            json_data = st.session_state.last_df.to_json(orient="records", indent=2)
            st.download_button("JSON", json_data, "export.json", "application/json", use_container_width=True)
    else:
        st.caption("Esegui una query per abilitare l'export")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Database Schema
    with st.expander("📊 Schema Database"):
        st.markdown("""
        **customers**  
        `id` `name` `segment` `country` `city` `state` `region`
        
        **products**  
        `id` `name` `category` `sub_category`
        
        **orders**  
        `id` `customer_id` `order_date` `ship_date` `total`
        
        **order_items**  
        `order_id` `product_id` `quantity` `sales` `profit`
        """)

# =============================================================================
# MAIN CONTENT
# =============================================================================

# Hero Section (only when no results)
if st.session_state.last_result is None:
    st.markdown("""
        <div style="text-align: center; padding: 60px 20px; margin-bottom: 32px;">
            <h1 style="font-size: 48px; font-weight: 700; margin-bottom: 16px; background: linear-gradient(135deg, #ffffff, #9ca3af); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                DataPulse
            </h1>
            <p style="font-size: 18px; color: #9ca3af; max-width: 500px; margin: 0 auto; line-height: 1.6;">
                Interroga i tuoi dati in linguaggio naturale.<br>L'AI genera query SQL e visualizzazioni automatiche.
            </p>
        </div>
    """, unsafe_allow_html=True)

# Query Input Section
st.markdown("### 💬 Fai una domanda")

col1, col2 = st.columns([5, 1])

with col1:
    question = st.text_input(
        "query",
        placeholder="Es: Qual è il fatturato totale per regione?",
        label_visibility="collapsed"
    )

with col2:
    submit = st.button("Analizza", type="primary", use_container_width=True)

# Quick suggestions (only when no results)
if st.session_state.last_result is None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 💡 Suggerimenti")
    
    suggestions = [
        ("📊 Totale Vendite", "Qual è il totale delle vendite?"),
        ("🌍 Per Regione", "Mostra il fatturato per regione"),
        ("🏆 Top Prodotti", "Quali sono i 5 prodotti più venduti?"),
        ("📈 Ordini", "Quanti ordini ci sono in totale?")
    ]
    
    cols = st.columns(4)
    for i, (label, query) in enumerate(suggestions):
        with cols[i]:
            if st.button(label, key=f"sug_{i}", use_container_width=True):
                st.session_state["_pending_query"] = query
                st.rerun()

# Handle pending query from suggestions
if "_pending_query" in st.session_state:
    question = st.session_state["_pending_query"]
    del st.session_state["_pending_query"]
    submit = True

# =============================================================================
# QUERY EXECUTION
# =============================================================================

if submit and question:
    if not question.strip():
        st.warning("⚠️ Inserisci una domanda valida")
    elif len(question) < 5:
        st.warning("⚠️ La domanda è troppo corta")
    else:
        with st.spinner("⚡ Analisi in corso..."):
            start_time = time.time()
            result = send_query(question)
            elapsed = time.time() - start_time
            st.session_state.query_time = elapsed
        
        if "error" in result:
            st.session_state.last_result = {"error": result["error"]}
            st.session_state.last_sql = result.get("generated_sql")
            st.session_state.last_df = None
            add_to_history(question, False)
        else:
            st.session_state.last_result = result
            st.session_state.last_sql = result.get("generated_sql", "N/A")
            st.session_state.last_df = pd.DataFrame(result.get("data", []))
            add_to_history(question, True)
        
        st.rerun()

# =============================================================================
# RESULTS DISPLAY
# =============================================================================

if st.session_state.last_result is not None:
    result = st.session_state.last_result
    
    st.markdown("---")
    
    if "error" in result:
        # Error display
        st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 20px; margin: 16px 0;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 36px; height: 36px; background: #ef4444; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">✕</div>
                    <div>
                        <div style="color: #ef4444; font-weight: 600; font-size: 16px;">Errore nell'analisi</div>
                        <div style="color: #9ca3af; font-size: 14px; margin-top: 4px;">{result["error"]}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.last_sql:
            with st.expander("🔍 SQL generato (debug)"):
                st.code(st.session_state.last_sql, language="sql")
    else:
        # Success display
        df = st.session_state.last_df
        query_time = st.session_state.query_time or 0
        
        st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 16px 20px; margin: 16px 0;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 36px; height: 36px; background: #10b981; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">✓</div>
                    <div>
                        <div style="color: #10b981; font-weight: 600;">Query completata</div>
                        <div style="color: #6b7280; font-size: 13px;">{len(df)} righe • {len(df.columns)} colonne • {query_time:.2f}s</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabs for results
        tab_chart, tab_table, tab_sql = st.tabs(["📊 Grafico", "📋 Tabella", "💻 SQL"])
        
        with tab_chart:
            if not df.empty:
                col_opt, col_viz = st.columns([1, 4])
                
                with col_opt:
                    auto_type = detect_chart_type(df)
                    options = ["Auto", "Barre", "Torta", "Linea", "Scatter", "Tabella", "Metrica"]
                    choice = st.selectbox("Tipo", options, index=0)
                    
                    type_map = {
                        "Auto": auto_type,
                        "Barre": "bar",
                        "Torta": "pie",
                        "Linea": "line",
                        "Scatter": "scatter",
                        "Tabella": "table",
                        "Metrica": "metric"
                    }
                    final_type = type_map.get(choice, "table")
                
                with col_viz:
                    create_chart(df, final_type)
            else:
                st.info("Nessun dato da visualizzare")
        
        with tab_table:
            if not df.empty:
                st.dataframe(df, use_container_width=True, height=450)
            else:
                st.warning("La query non ha restituito risultati")
        
        with tab_sql:
            st.markdown("##### SQL Generato")
            st.code(st.session_state.last_sql, language="sql")
            
            if not df.empty:
                st.markdown("##### Struttura Dati")
                schema_df = pd.DataFrame({
                    "Colonna": df.columns,
                    "Tipo": [str(t) for t in df.dtypes]
                })
                st.dataframe(schema_df, use_container_width=True, hide_index=True)

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; padding: 24px; border-top: 1px solid #2a2a32; color: #6b7280; font-size: 13px;">
        DataPulse AI Analytics
    </div>
""", unsafe_allow_html=True)
