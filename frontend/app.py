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
import time
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
# DESIGN SYSTEM - PREMIUM UI/UX
# ============================================================================

# CSS Variables e Design System completo
st.markdown("""
<style>
    /* ========================================
       CSS VARIABLES - DESIGN TOKENS
       ======================================== */
    :root {
        /* Color Palette - Premium Dark Theme */
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-tertiary: #1a1a2e;
        --bg-card: rgba(26, 26, 46, 0.7);
        --bg-glass: rgba(255, 255, 255, 0.03);
        
        /* Accent Colors - Vibrant Gradient */
        --accent-primary: #667eea;
        --accent-secondary: #764ba2;
        --accent-tertiary: #f093fb;
        --accent-success: #00d4aa;
        --accent-warning: #ffc107;
        --accent-error: #ff6b6b;
        
        /* Text Colors */
        --text-primary: #ffffff;
        --text-secondary: #a0a0b0;
        --text-muted: #6c6c7c;
        
        /* Borders & Shadows */
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-accent: rgba(102, 126, 234, 0.4);
        --shadow-glow: 0 0 40px rgba(102, 126, 234, 0.15);
        --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.3);
        
        /* Spacing */
        --space-xs: 0.25rem;
        --space-sm: 0.5rem;
        --space-md: 1rem;
        --space-lg: 1.5rem;
        --space-xl: 2rem;
        --space-2xl: 3rem;
        
        /* Border Radius */
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 24px;
        
        /* Transitions */
        --transition-fast: 0.15s ease;
        --transition-normal: 0.3s ease;
        --transition-slow: 0.5s ease;
    }

    /* ========================================
       GLOBAL STYLES & TYPOGRAPHY
       ======================================== */
    
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 50%, var(--bg-tertiary) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ========================================
       HEADER STYLES
       ======================================== */
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 50%, var(--accent-tertiary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        text-shadow: 0 0 80px rgba(102, 126, 234, 0.5);
        animation: headerGlow 3s ease-in-out infinite alternate;
    }
    
    @keyframes headerGlow {
        from { filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.3)); }
        to { filter: drop-shadow(0 0 40px rgba(118, 75, 162, 0.4)); }
    }
    
    .sub-header {
        text-align: center;
        color: var(--text-secondary);
        font-size: 1.15rem;
        font-weight: 400;
        margin-bottom: var(--space-xl);
        letter-spacing: 0.02em;
    }
    
    .sub-header span {
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 600;
    }

    /* ========================================
       GLASS MORPHISM CARDS
       ======================================== */
    
    .glass-card {
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: var(--space-lg);
        box-shadow: var(--shadow-card);
        transition: all var(--transition-normal);
    }
    
    .glass-card:hover {
        border-color: var(--border-accent);
        box-shadow: var(--shadow-glow), var(--shadow-card);
        transform: translateY(-2px);
    }
    
    .glass-card-header {
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        margin-bottom: var(--space-md);
        padding-bottom: var(--space-md);
        border-bottom: 1px solid var(--border-subtle);
    }
    
    .glass-card-header h3 {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .glass-card-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }

    /* ========================================
       PREMIUM INPUT STYLES
       ======================================== */
    
    /* Text Input with Glow Effect */
    .stTextInput > div > div > input {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        padding: var(--space-md) var(--space-lg) !important;
        transition: all var(--transition-normal) !important;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15), 
                    0 0 30px rgba(102, 126, 234, 0.2) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--text-muted) !important;
    }

    /* ========================================
       PREMIUM BUTTON STYLES
       ======================================== */
    
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.875rem 2rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em !important;
        transition: all var(--transition-normal) !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Secondary Button Style */
    .secondary-btn > button {
        background: transparent !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-secondary) !important;
        box-shadow: none !important;
    }
    
    .secondary-btn > button:hover {
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        background: rgba(102, 126, 234, 0.1) !important;
    }

    /* ========================================
       SIDEBAR PREMIUM STYLES
       ======================================== */
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown h2 {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.01em;
    }
    
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: var(--space-lg) !important;
    }
    
    /* Sidebar Divider */
    [data-testid="stSidebar"] hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, var(--border-subtle), transparent) !important;
        margin: var(--space-lg) 0 !important;
    }

    /* ========================================
       SELECT BOX & DROPDOWN STYLES
       ======================================== */
    
    .stSelectbox > div > div {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: var(--accent-primary) !important;
    }

    /* ========================================
       EXPANDER STYLES
       ======================================== */
    
    .streamlit-expanderHeader {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--accent-primary) !important;
        color: var(--text-primary) !important;
    }

    /* ========================================
       CODE BLOCK STYLES (SQL)
       ======================================== */
    
    .stCodeBlock {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-subtle) !important;
        overflow: hidden;
    }
    
    .stCodeBlock pre {
        background: rgba(13, 17, 23, 0.8) !important;
        backdrop-filter: blur(10px);
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 0.875rem !important;
        line-height: 1.6 !important;
        padding: var(--space-lg) !important;
    }

    /* ========================================
       DATAFRAME / TABLE STYLES
       ======================================== */
    
    .stDataFrame {
        border-radius: var(--radius-md) !important;
        overflow: hidden;
        border: 1px solid var(--border-subtle) !important;
    }
    
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: var(--bg-glass) !important;
    }

    /* ========================================
       METRIC CARD STYLES
       ======================================== */
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--bg-glass) 0%, rgba(102, 126, 234, 0.1) 100%);
        border: 1px solid var(--border-accent);
        border-radius: var(--radius-lg);
        padding: var(--space-lg);
        text-align: center;
    }
    
    [data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-tertiary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ========================================
       ALERT & MESSAGE STYLES
       ======================================== */
    
    .stSuccess {
        background: rgba(0, 212, 170, 0.1) !important;
        border: 1px solid rgba(0, 212, 170, 0.3) !important;
        border-radius: var(--radius-md) !important;
        color: var(--accent-success) !important;
    }
    
    .stWarning {
        background: rgba(255, 193, 7, 0.1) !important;
        border: 1px solid rgba(255, 193, 7, 0.3) !important;
        border-radius: var(--radius-md) !important;
    }
    
    .stError {
        background: rgba(255, 107, 107, 0.1) !important;
        border: 1px solid rgba(255, 107, 107, 0.3) !important;
        border-radius: var(--radius-md) !important;
    }
    
    .stInfo {
        background: rgba(102, 126, 234, 0.1) !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        border-radius: var(--radius-md) !important;
    }

    /* ========================================
       RADIO BUTTONS (Visualization Toggle)
       ======================================== */
    
    .stRadio > div {
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: var(--space-sm) var(--space-md);
        display: inline-flex;
        gap: var(--space-xs);
    }
    
    .stRadio > div > label {
        background: transparent !important;
        border-radius: var(--radius-sm) !important;
        padding: var(--space-sm) var(--space-md) !important;
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        transition: all var(--transition-fast) !important;
        cursor: pointer;
    }
    
    .stRadio > div > label:hover {
        color: var(--text-primary) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    
    .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
    }

    /* ========================================
       SPINNER / LOADING STYLES
       ======================================== */
    
    .stSpinner > div {
        border-color: var(--accent-primary) transparent transparent transparent !important;
    }

    /* ========================================
       DOWNLOAD BUTTON STYLES
       ======================================== */
    
    .stDownloadButton > button {
        background: transparent !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-secondary) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 500 !important;
        transition: all var(--transition-normal) !important;
    }
    
    .stDownloadButton > button:hover {
        border-color: var(--accent-success) !important;
        color: var(--accent-success) !important;
        background: rgba(0, 212, 170, 0.1) !important;
    }

    /* ========================================
       CUSTOM SECTION HEADERS
       ======================================== */
    
    .section-header {
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        margin-bottom: var(--space-md);
    }
    
    .section-header-icon {
        width: 36px;
        height: 36px;
        border-radius: var(--radius-sm);
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }
    
    .section-header-text {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    /* ========================================
       FOOTER STYLES
       ======================================== */
    
    .premium-footer {
        text-align: center;
        padding: var(--space-xl) 0;
        margin-top: var(--space-2xl);
        border-top: 1px solid var(--border-subtle);
    }
    
    .premium-footer p {
        color: var(--text-muted);
        font-size: 0.85rem;
        margin: var(--space-xs) 0;
    }
    
    .premium-footer .brand {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    .tech-badges {
        display: flex;
        justify-content: center;
        gap: var(--space-sm);
        margin-top: var(--space-md);
        flex-wrap: wrap;
    }
    
    .tech-badge {
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.75rem;
        color: var(--text-secondary);
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    /* ========================================
       SCROLLBAR STYLES
       ======================================== */
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-subtle);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-primary);
    }

    /* ========================================
       ANIMATIONS
       ======================================== */
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.3); }
        50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.6); }
    }
    
    .animate-fade-in {
        animation: fadeInUp 0.5s ease forwards;
    }
    
    .animate-pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    .animate-glow {
        animation: glow 2s ease-in-out infinite;
    }

    /* ========================================
       RESPONSIVE DESIGN
       ======================================== */
    
    /* Tablet */
    @media (max-width: 1024px) {
        .main-header {
            font-size: 2.5rem !important;
        }
        
        .sub-header {
            font-size: 1rem !important;
        }
        
        [data-testid="stSidebar"] {
            min-width: 280px !important;
        }
    }
    
    /* Mobile */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
        }
        
        .sub-header {
            font-size: 0.9rem !important;
        }
        
        .stButton > button {
            padding: 0.6rem 1rem !important;
            font-size: 0.85rem !important;
        }
        
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
        }
        
        .tech-badges {
            gap: 0.25rem !important;
        }
        
        .tech-badge {
            font-size: 0.65rem !important;
            padding: 3px 8px !important;
        }
    }
    
    /* Small Mobile */
    @media (max-width: 480px) {
        .main-header {
            font-size: 1.75rem !important;
        }
        
        :root {
            --space-lg: 1rem;
            --space-xl: 1.5rem;
        }
    }

    /* ========================================
       SQL CODE BLOCK PREMIUM
       ======================================== */
    
    .sql-preview-container {
        position: relative;
        background: linear-gradient(135deg, rgba(13, 17, 23, 0.9) 0%, rgba(22, 27, 34, 0.9) 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        overflow: hidden;
    }
    
    .sql-preview-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        background: rgba(102, 126, 234, 0.1);
        border-bottom: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .sql-preview-header .language-tag {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .sql-preview-header .copy-btn {
        background: rgba(255, 255, 255, 0.1);
        border: none;
        color: #a0a0b0;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .sql-preview-header .copy-btn:hover {
        background: rgba(102, 126, 234, 0.3);
        color: #ffffff;
    }

    /* ========================================
       FOCUS STATES (Accessibility)
       ======================================== */
    
    .stButton > button:focus-visible,
    .stTextInput > div > div > input:focus-visible,
    .stSelectbox > div > div:focus-visible {
        outline: 2px solid var(--accent-primary) !important;
        outline-offset: 2px !important;
    }

    /* ========================================
       PRINT STYLES
       ======================================== */
    
    @media print {
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        .stButton {
            display: none !important;
        }
        
        .premium-footer {
            display: none !important;
        }
    }

    /* ========================================
       TRANSITIONS (Smooth UI)
       ======================================== */
    
    * {
        transition-property: background-color, border-color, color, fill, stroke, opacity, box-shadow, transform;
        transition-duration: 0.15s;
        transition-timing-function: ease;
    }
    
    /* Disable transitions for elements that shouldn't animate */
    .stSpinner, .stSpinner * {
        transition: none !important;
    }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .animate-fade-in {
        animation: fadeInUp 0.5s ease forwards;
    }
    
    .animate-pulse {
        animation: pulse 2s ease-in-out infinite;
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
    if "selected_chip" not in st.session_state:
        st.session_state.selected_chip = None  # Chip selezionato
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False  # Stato loading
    if "last_query_time" not in st.session_state:
        st.session_state.last_query_time = None  # Tempo ultima query

init_session_state()

# ============================================================================
# FUNZIONI HELPER
# ============================================================================

def get_smart_suggestions() -> List[Dict[str, str]]:
    """
    Restituisce suggerimenti intelligenti categorizzati.
    Returns: Lista di dizionari con categoria, icona e domanda.
    """
    return [
        {"category": "📊 Vendite", "questions": [
            "Qual è il totale delle vendite?",
            "Vendite per regione",
            "Top 10 prodotti per fatturato",
            "Vendite mensili ultimo anno"
        ]},
        {"category": "👥 Clienti", "questions": [
            "Quanti clienti ci sono?",
            "Clienti per segmento",
            "Top clienti per spesa",
            "Nuovi clienti per mese"
        ]},
        {"category": "📦 Prodotti", "questions": [
            "Prodotti più venduti",
            "Categorie prodotto",
            "Prodotti con margine alto",
            "Inventario per categoria"
        ]},
        {"category": "📈 Trend", "questions": [
            "Andamento vendite mensile",
            "Crescita anno su anno",
            "Stagionalità ordini",
            "Performance per trimestre"
        ]}
    ]


def render_loading_animation():
    """Renderizza un'animazione di loading elegante."""
    st.markdown("""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem;
    ">
        <div style="
            width: 60px;
            height: 60px;
            border: 3px solid rgba(102, 126, 234, 0.1);
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 1.5rem;
        "></div>
        <div style="
            font-size: 1rem;
            color: #a0a0b0;
            margin-bottom: 0.5rem;
        ">🤖 L'AI sta elaborando la tua richiesta...</div>
        <div style="
            font-size: 0.8rem;
            color: #6c6c7c;
        ">Generazione SQL • Esecuzione Query • Analisi Risultati</div>
    </div>
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    """, unsafe_allow_html=True)


def render_skeleton_loader():
    """Renderizza uno skeleton loader per i risultati."""
    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
    ">
        <div style="
            height: 20px;
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.1) 25%, rgba(102, 126, 234, 0.2) 50%, rgba(102, 126, 234, 0.1) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 4px;
            margin-bottom: 1rem;
            width: 60%;
        "></div>
        <div style="
            height: 200px;
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.05) 25%, rgba(102, 126, 234, 0.1) 50%, rgba(102, 126, 234, 0.05) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 8px;
        "></div>
    </div>
    <style>
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
    </style>
    """, unsafe_allow_html=True)


def calculate_query_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcola statistiche sulla query eseguita.
    Returns: Dizionario con statistiche.
    """
    if df is None or df.empty:
        return {"rows": 0, "cols": 0, "memory": "0 B"}
    
    memory_bytes = df.memory_usage(deep=True).sum()
    if memory_bytes < 1024:
        memory_str = f"{memory_bytes} B"
    elif memory_bytes < 1024 * 1024:
        memory_str = f"{memory_bytes / 1024:.1f} KB"
    else:
        memory_str = f"{memory_bytes / (1024 * 1024):.1f} MB"
    
    return {
        "rows": len(df),
        "cols": len(df.columns),
        "memory": memory_str,
        "numeric_cols": len(df.select_dtypes(include=['number']).columns),
        "text_cols": len(df.select_dtypes(include=['object']).columns)
    }


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
    Returns: 'bar', 'pie', 'line', 'table', 'metric', 'area', 'scatter'
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
        if num_rows <= 6:
            return "pie"
        elif num_rows <= 20:
            return "bar"
        else:
            return "table"
    
    # Time series (date nel nome colonna)
    date_cols = [c for c in df.columns if any(d in c.lower() for d in ['date', 'month', 'year', 'time', 'period'])]
    if date_cols and len(numeric_cols) >= 1:
        return "area" if num_rows > 10 else "line"
    
    # Scatter plot per correlazioni
    if len(numeric_cols) >= 2 and num_rows > 5:
        return "scatter"
    
    # Default: tabella
    return "table"


# ============================================================================
# PLOTLY THEME PREMIUM
# ============================================================================

def get_plotly_theme() -> dict:
    """
    Restituisce un tema Plotly personalizzato premium.
    """
    return {
        'layout': {
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'font': {
                'family': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                'color': '#a0a0b0',
                'size': 12
            },
            'title': {
                'font': {
                    'size': 16,
                    'color': '#ffffff',
                    'family': 'Inter, sans-serif'
                },
                'x': 0.5,
                'xanchor': 'center'
            },
            'xaxis': {
                'gridcolor': 'rgba(255,255,255,0.05)',
                'linecolor': 'rgba(255,255,255,0.1)',
                'tickfont': {'color': '#6c6c7c'},
                'title': {'font': {'color': '#a0a0b0'}}
            },
            'yaxis': {
                'gridcolor': 'rgba(255,255,255,0.05)',
                'linecolor': 'rgba(255,255,255,0.1)',
                'tickfont': {'color': '#6c6c7c'},
                'title': {'font': {'color': '#a0a0b0'}}
            },
            'legend': {
                'bgcolor': 'rgba(0,0,0,0.3)',
                'bordercolor': 'rgba(255,255,255,0.1)',
                'font': {'color': '#a0a0b0'}
            },
            'hoverlabel': {
                'bgcolor': '#1a1a2e',
                'bordercolor': '#667eea',
                'font': {'color': '#ffffff', 'size': 13}
            },
            'margin': {'t': 60, 'b': 40, 'l': 60, 'r': 20}
        }
    }


# Palette colori premium
PREMIUM_COLORS = [
    '#667eea',  # Primary purple
    '#764ba2',  # Secondary purple
    '#00d4aa',  # Teal/Success
    '#f093fb',  # Pink
    '#4facfe',  # Light blue
    '#ffc107',  # Amber
    '#ff6b6b',  # Coral
    '#a8edea',  # Mint
    '#fed6e3',  # Blush
    '#d299c2',  # Mauve
]


def create_visualization(df: pd.DataFrame, chart_type: str, sql: str):
    """
    Crea visualizzazioni premium con stile enterprise.
    """
    if df is None or df.empty:
        render_empty_state()
        return
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    theme = get_plotly_theme()
    
    if chart_type == "metric":
        render_metric_card(df)
        
    elif chart_type == "bar":
        render_bar_chart(df, categorical_cols, numeric_cols, theme)
            
    elif chart_type == "pie":
        render_pie_chart(df, categorical_cols, numeric_cols, theme)
            
    elif chart_type == "line":
        render_line_chart(df, numeric_cols, theme)
    
    elif chart_type == "area":
        render_area_chart(df, numeric_cols, theme)
    
    elif chart_type == "scatter":
        render_scatter_chart(df, numeric_cols, categorical_cols, theme)
    
    else:
        # Default: tabella premium
        render_premium_table(df)


def render_empty_state():
    """Renderizza uno stato vuoto elegante."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        border: 2px dashed rgba(102, 126, 234, 0.2);
        border-radius: 16px;
        padding: 4rem 2rem;
        text-align: center;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;">📭</div>
        <h3 style="color: #ffffff; margin-bottom: 0.5rem;">Nessun dato disponibile</h3>
        <p style="color: #6c6c7c; font-size: 0.9rem;">
            La query non ha restituito risultati.<br>
            Prova a modificare i parametri di ricerca.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(df: pd.DataFrame):
    """Renderizza un singolo valore come card metrica premium."""
    value = df.iloc[0, 0]
    col_name = df.columns[0]
    
    # Formatta il valore
    if isinstance(value, (int, float)):
        if value >= 1000000:
            formatted_value = f"{value/1000000:.1f}M"
        elif value >= 1000:
            formatted_value = f"{value/1000:.1f}K"
        else:
            formatted_value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
    else:
        formatted_value = str(value)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: -30px;
            right: -30px;
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, rgba(102, 126, 234, 0.2) 0%, transparent 70%);
            border-radius: 50%;
        "></div>
        <div style="
            font-size: 0.75rem;
            color: #6c6c7c;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 0.75rem;
        ">{col_name}</div>
        <div style="
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
        ">{formatted_value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_bar_chart(df: pd.DataFrame, categorical_cols: list, numeric_cols: list, theme: dict):
    """Renderizza un bar chart premium."""
    if not categorical_cols or not numeric_cols:
        render_premium_table(df)
        return
    
    fig = go.Figure()
    
    # Aggiungi barre con gradiente simulato
    fig.add_trace(go.Bar(
        x=df[categorical_cols[0]],
        y=df[numeric_cols[0]],
        marker=dict(
            color=df[numeric_cols[0]],
            colorscale=[[0, '#667eea'], [0.5, '#764ba2'], [1, '#f093fb']],
            line=dict(width=0),
            cornerradius=6
        ),
        hovertemplate='<b>%{x}</b><br>%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        **theme['layout'],
        title=dict(text=f'{numeric_cols[0]} per {categorical_cols[0]}', **theme['layout']['title']),
        showlegend=False,
        bargap=0.3,
        height=400
    )
    
    # Animazione
    fig.update_traces(marker_line_width=0)
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_pie_chart(df: pd.DataFrame, categorical_cols: list, numeric_cols: list, theme: dict):
    """Renderizza un donut chart premium."""
    if not categorical_cols or not numeric_cols:
        render_premium_table(df)
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=df[categorical_cols[0]],
        values=df[numeric_cols[0]],
        hole=0.55,
        marker=dict(
            colors=PREMIUM_COLORS[:len(df)],
            line=dict(color='rgba(0,0,0,0.3)', width=2)
        ),
        textinfo='percent',
        textfont=dict(size=13, color='white'),
        hovertemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>',
        pull=[0.02] * len(df)  # Leggero distacco
    ))
    
    fig.update_layout(
        **theme['layout'],
        title=dict(text=f'Distribuzione {numeric_cols[0]}', **theme['layout']['title']),
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='left',
            x=1.02,
            **theme['layout']['legend']
        ),
        height=400,
        annotations=[dict(
            text=f'<b>Totale</b><br>{df[numeric_cols[0]].sum():,.0f}',
            x=0.5, y=0.5,
            font=dict(size=14, color='#ffffff'),
            showarrow=False
        )]
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_line_chart(df: pd.DataFrame, numeric_cols: list, theme: dict):
    """Renderizza un line chart premium con markers."""
    date_cols = [c for c in df.columns if any(d in c.lower() for d in ['date', 'month', 'year', 'time', 'period'])]
    x_col = date_cols[0] if date_cols else df.columns[0]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[numeric_cols[0]],
        mode='lines+markers',
        line=dict(color='#667eea', width=3, shape='spline'),
        marker=dict(
            size=10,
            color='#667eea',
            line=dict(color='white', width=2)
        ),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.1)',
        hovertemplate='<b>%{x}</b><br>%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        **theme['layout'],
        title=dict(text=f'Trend {numeric_cols[0]}', **theme['layout']['title']),
        showlegend=False,
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_area_chart(df: pd.DataFrame, numeric_cols: list, theme: dict):
    """Renderizza un area chart premium con gradiente."""
    date_cols = [c for c in df.columns if any(d in c.lower() for d in ['date', 'month', 'year', 'time', 'period'])]
    x_col = date_cols[0] if date_cols else df.columns[0]
    
    fig = go.Figure()
    
    # Area con gradiente
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[numeric_cols[0]],
        mode='lines',
        line=dict(color='#667eea', width=2),
        fill='tozeroy',
        fillgradient=dict(
            type='vertical',
            colorscale=[[0, 'rgba(102, 126, 234, 0)'], [1, 'rgba(102, 126, 234, 0.3)']]
        ),
        hovertemplate='<b>%{x}</b><br>%{y:,.0f}<extra></extra>'
    ))
    
    # Linea superiore più definita
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[numeric_cols[0]],
        mode='lines',
        line=dict(color='#764ba2', width=3, shape='spline'),
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        **theme['layout'],
        title=dict(text=f'Andamento {numeric_cols[0]}', **theme['layout']['title']),
        showlegend=False,
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_scatter_chart(df: pd.DataFrame, numeric_cols: list, categorical_cols: list, theme: dict):
    """Renderizza uno scatter plot premium."""
    if len(numeric_cols) < 2:
        render_premium_table(df)
        return
    
    fig = go.Figure()
    
    # Colore per categoria se disponibile
    if categorical_cols:
        categories = df[categorical_cols[0]].unique()
        for i, cat in enumerate(categories):
            mask = df[categorical_cols[0]] == cat
            fig.add_trace(go.Scatter(
                x=df[mask][numeric_cols[0]],
                y=df[mask][numeric_cols[1]],
                mode='markers',
                name=str(cat),
                marker=dict(
                    size=12,
                    color=PREMIUM_COLORS[i % len(PREMIUM_COLORS)],
                    line=dict(color='white', width=1),
                    opacity=0.8
                ),
                hovertemplate=f'<b>{cat}</b><br>{numeric_cols[0]}: %{{x:,.0f}}<br>{numeric_cols[1]}: %{{y:,.0f}}<extra></extra>'
            ))
    else:
        fig.add_trace(go.Scatter(
            x=df[numeric_cols[0]],
            y=df[numeric_cols[1]],
            mode='markers',
            marker=dict(
                size=12,
                color=df[numeric_cols[1]],
                colorscale=[[0, '#667eea'], [1, '#f093fb']],
                line=dict(color='white', width=1),
                opacity=0.8
            ),
            hovertemplate=f'{numeric_cols[0]}: %{{x:,.0f}}<br>{numeric_cols[1]}: %{{y:,.0f}}<extra></extra>'
        ))
    
    fig.update_layout(
        **theme['layout'],
        title=dict(text=f'{numeric_cols[0]} vs {numeric_cols[1]}', **theme['layout']['title']),
        height=400,
        xaxis_title=numeric_cols[0],
        yaxis_title=numeric_cols[1]
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_premium_table(df: pd.DataFrame):
    """Renderizza una tabella dati premium con styling avanzato."""
    # Header della tabella
    st.markdown("""
    <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    ">
        <div style="
            font-size: 0.75rem;
            color: #6c6c7c;
            display: flex;
            align-items: center;
            gap: 1rem;
        ">
            <span>📋 Visualizzazione tabella</span>
            <span style="
                background: rgba(102, 126, 234, 0.15);
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.7rem;
            ">{} righe × {} colonne</span>
        </div>
    </div>
    """.format(len(df), len(df.columns)), unsafe_allow_html=True)
    
    # Styling per il dataframe
    styled_df = df.style.set_properties(**{
        'background-color': 'rgba(0, 0, 0, 0.2)',
        'color': '#a0a0b0',
        'border-color': 'rgba(255, 255, 255, 0.05)'
    }).set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', 'rgba(102, 126, 234, 0.2)'),
            ('color', '#ffffff'),
            ('font-weight', '600'),
            ('text-transform', 'uppercase'),
            ('font-size', '0.75rem'),
            ('letter-spacing', '0.05em'),
            ('padding', '12px 16px'),
            ('border-bottom', '2px solid rgba(102, 126, 234, 0.3)')
        ]},
        {'selector': 'td', 'props': [
            ('padding', '10px 16px'),
            ('border-bottom', '1px solid rgba(255, 255, 255, 0.05)')
        ]},
        {'selector': 'tr:hover td', 'props': [
            ('background-color', 'rgba(102, 126, 234, 0.1)')
        ]}
    ])
    
    # Formatta numeri
    for col in df.select_dtypes(include=['number']).columns:
        styled_df = styled_df.format({col: '{:,.2f}'})
    
    st.dataframe(
        df, 
        use_container_width=True,
        height=min(400, 50 + len(df) * 35)  # Altezza dinamica
    )
    
    # Quick stats footer
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-top: 0.5rem;
            display: flex;
            gap: 2rem;
            font-size: 0.75rem;
            color: #6c6c7c;
        ">
        """, unsafe_allow_html=True)
        
        stats_cols = st.columns(min(4, len(numeric_cols)))
        for i, col in enumerate(numeric_cols[:4]):
            with stats_cols[i]:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="color: #6c6c7c; font-size: 0.65rem; text-transform: uppercase;">Σ {col[:15]}</div>
                    <div style="color: #667eea; font-weight: 600;">{df[col].sum():,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


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
# SIDEBAR PREMIUM
# ============================================================================

with st.sidebar:
    # Logo e Brand Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 1.5rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
        <h1 style="
            font-size: 1.5rem; 
            font-weight: 800; 
            margin: 0;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        ">DataPulse</h1>
        <p style="
            font-size: 0.75rem; 
            color: #6c6c7c; 
            margin: 0.25rem 0 0 0;
            letter-spacing: 0.05em;
        ">AI-Powered Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Status Connessione API
    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div style="
                width: 8px; 
                height: 8px; 
                background: #00d4aa; 
                border-radius: 50%;
                box-shadow: 0 0 8px #00d4aa;
            "></div>
            <span style="font-size: 0.8rem; color: #a0a0b0;">Sistema Operativo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sezione: Quick Actions
    st.markdown("""
    <div style="
        font-size: 0.7rem;
        font-weight: 600;
        color: #6c6c7c;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    ">⚡ Azioni Rapide</div>
    """, unsafe_allow_html=True)
    
    # Domande di esempio come chip cliccabili
    example_questions = get_example_questions()
    selected_example = st.selectbox(
        "Seleziona una domanda:",
        ["-- Seleziona esempio --"] + example_questions,
        key="example_selector",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Sezione: Cronologia Query - Timeline Premium
    st.markdown("""
    <div style="
        font-size: 0.7rem;
        font-weight: 600;
        color: #6c6c7c;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    ">
        <span>📜 Cronologia Recente</span>
        <span style="
            background: rgba(102, 126, 234, 0.2);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.65rem;
        ">{} query</span>
    </div>
    """.format(len(st.session_state.query_history)), unsafe_allow_html=True)
    
    if st.session_state.query_history:
        # Timeline verticale premium
        for i, entry in enumerate(st.session_state.query_history[:5]):
            status_color = "#00d4aa" if entry["success"] else "#ff6b6b"
            status_icon = "✓" if entry["success"] else "✗"
            status_bg = "rgba(0, 212, 170, 0.15)" if entry["success"] else "rgba(255, 107, 107, 0.15)"
            
            # Card per ogni entry della cronologia
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-left: 3px solid {status_color};
                border-radius: 0 8px 8px 0;
                padding: 0.75rem;
                margin-bottom: 0.5rem;
                transition: all 0.2s ease;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                    <span style="
                        background: {status_bg};
                        color: {status_color};
                        width: 18px;
                        height: 18px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 0.65rem;
                        font-weight: bold;
                    ">{status_icon}</span>
                    <span style="font-size: 0.7rem; color: #6c6c7c;">{entry['timestamp']}</span>
                </div>
                <div style="
                    font-size: 0.8rem; 
                    color: #a0a0b0;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                ">{entry['question']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # SQL in expander
            with st.expander(f"🔧 Vedi SQL", expanded=False):
                st.code(entry["sql"], language="sql")
    else:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        ">
            <div style="
                width: 50px;
                height: 50px;
                background: rgba(102, 126, 234, 0.15);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 0.75rem auto;
                font-size: 1.5rem;
            ">🔍</div>
            <p style="font-size: 0.85rem; color: #a0a0b0; margin: 0 0 0.25rem 0; font-weight: 500;">
                Nessuna query ancora
            </p>
            <p style="font-size: 0.75rem; color: #6c6c7c; margin: 0;">
                Inizia a esplorare i tuoi dati!
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.query_history:
        st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
        col_clear, col_export_hist = st.columns(2)
        with col_clear:
            if st.button("🗑️ Cancella", use_container_width=True, key="clear_history"):
                st.session_state.query_history = []
                st.rerun()
        with col_export_hist:
            # Export cronologia come JSON
            if st.button("📤 Esporta", use_container_width=True, key="export_history"):
                import json
                history_json = json.dumps(st.session_state.query_history, indent=2, ensure_ascii=False)
                st.download_button(
                    "💾 Scarica",
                    history_json,
                    f"datapulse_history_{datetime.now().strftime('%Y%m%d')}.json",
                    "application/json"
                )
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sezione: Export
    st.markdown("""
    <div style="
        font-size: 0.7rem;
        font-weight: 600;
        color: #6c6c7c;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    ">💾 Esporta Risultati</div>
    """, unsafe_allow_html=True)
    
    if st.session_state.current_df is not None and not st.session_state.current_df.empty:
        csv = st.session_state.current_df.to_csv(index=False)
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button(
                label="📥 CSV",
                data=csv,
                file_name=f"datapulse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_exp2:
            # JSON export
            json_data = st.session_state.current_df.to_json(orient="records", indent=2)
            st.download_button(
                label="📋 JSON",
                data=json_data,
                file_name=f"datapulse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.03);
            border: 1px dashed rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        ">
            <p style="font-size: 0.8rem; color: #6c6c7c; margin: 0;">
                Esegui una query per<br>abilitare l'export
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Database Schema Info
    st.markdown("""
    <div style="
        font-size: 0.7rem;
        font-weight: 600;
        color: #6c6c7c;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    ">🗄️ Schema Database</div>
    """, unsafe_allow_html=True)
    
    with st.expander("📋 Tabelle disponibili", expanded=False):
        st.markdown("""
        <div style="font-size: 0.8rem; line-height: 1.8;">
            <code style="background: rgba(102, 126, 234, 0.2); padding: 2px 6px; border-radius: 4px;">customers</code> - Anagrafica clienti<br>
            <code style="background: rgba(102, 126, 234, 0.2); padding: 2px 6px; border-radius: 4px;">products</code> - Catalogo prodotti<br>
            <code style="background: rgba(102, 126, 234, 0.2); padding: 2px 6px; border-radius: 4px;">orders</code> - Ordini<br>
            <code style="background: rgba(102, 126, 234, 0.2); padding: 2px 6px; border-radius: 4px;">order_items</code> - Dettagli ordine
        </div>
        """, unsafe_allow_html=True)
    
    # Footer Sidebar
    st.markdown("""
    <div style="
        position: absolute;
        bottom: 1rem;
        left: 1rem;
        right: 1rem;
        text-align: center;
        padding-top: 1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    ">
        <p style="font-size: 0.7rem; color: #4a4a5a; margin: 0;">
            v1.0.0 • MIT License
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header principale con animazione
st.markdown('''
<div class="animate-fade-in">
    <h1 class="main-header">📊 DataPulse</h1>
    <p class="sub-header">Interroga i tuoi dati aziendali con <span>intelligenza artificiale</span></p>
</div>
''', unsafe_allow_html=True)

# ============================================================================
# QUERY INTERFACE PREMIUM
# ============================================================================

# Main Search Container
st.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
    border: 1px solid rgba(102, 126, 234, 0.15);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
">
    <!-- Decorative gradient orb -->
    <div style="
        position: absolute;
        top: -50px;
        right: -50px;
        width: 150px;
        height: 150px;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.15) 0%, transparent 70%);
        border-radius: 50%;
    "></div>
""", unsafe_allow_html=True)

# Smart Suggestions - Categorized chips
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <div style="
        font-size: 0.7rem;
        font-weight: 600;
        color: #6c6c7c;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    ">💡 Suggerimenti rapidi</div>
</div>
""", unsafe_allow_html=True)

# Interactive chips row
chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)

with chip_col1:
    if st.button("📊 Vendite totali", key="chip_1", use_container_width=True):
        st.session_state.selected_chip = "Qual è il totale delle vendite?"
        
with chip_col2:
    if st.button("👥 Clienti per regione", key="chip_2", use_container_width=True):
        st.session_state.selected_chip = "Quanti clienti ci sono per regione?"
        
with chip_col3:
    if st.button("🏆 Top 10 prodotti", key="chip_3", use_container_width=True):
        st.session_state.selected_chip = "Quali sono i 10 prodotti più venduti?"
        
with chip_col4:
    if st.button("📈 Trend mensile", key="chip_4", use_container_width=True):
        st.session_state.selected_chip = "Mostra le vendite mensili"

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# Main Input Area with enhanced styling
st.markdown("""
<div style="
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 0.25rem;
">
""", unsafe_allow_html=True)

col_input, col_btn = st.columns([6, 1])

with col_input:
    # Determina il valore predefinito
    if st.session_state.selected_chip:
        default_value = st.session_state.selected_chip
        st.session_state.selected_chip = None  # Reset dopo l'uso
    elif selected_example != "-- Seleziona esempio --":
        default_value = selected_example
    else:
        default_value = ""
    
    question = st.text_input(
        "Fai una domanda sui tuoi dati",
        value=default_value,
        placeholder="🔍 Scrivi la tua domanda in linguaggio naturale...",
        key="main_question_input",
        label_visibility="collapsed"
    )

with col_btn:
    analyze_clicked = st.button("✨ Analizza", use_container_width=True, type="primary")

st.markdown("</div>", unsafe_allow_html=True)

# Character counter e tips
char_count = len(question) if question else 0
char_color = "#00d4aa" if char_count <= 400 else "#ffc107" if char_count <= 500 else "#ff6b6b"

st.markdown(f"""
<div style="
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.75rem;
    padding: 0 0.5rem;
">
    <span style="font-size: 0.7rem; color: #6c6c7c;">
        💡 Tip: Usa termini specifici come "totale", "media", "per categoria", "top 10"
    </span>
    <span style="font-size: 0.7rem; color: {char_color};">
        {char_count}/500
    </span>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# QUERY PROCESSING & FEEDBACK
# ============================================================================

if analyze_clicked:
    # Validazione input
    is_valid, error_msg = validate_question(question)
    
    if not is_valid:
        # Warning con stile custom
        st.markdown(f"""
        <div style="
            background: rgba(255, 193, 7, 0.1);
            border: 1px solid rgba(255, 193, 7, 0.3);
            border-left: 4px solid #ffc107;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin: 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        ">
            <span style="font-size: 1.5rem;">⚠️</span>
            <div>
                <div style="color: #ffc107; font-weight: 600; margin-bottom: 0.25rem;">Attenzione</div>
                <div style="color: #a0a0b0; font-size: 0.9rem;">{error_msg.replace('⚠️ ', '')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Loading state con animazione premium
        loading_placeholder = st.empty()
        
        with loading_placeholder.container():
            st.markdown("""
            <div style="
                background: rgba(102, 126, 234, 0.05);
                border: 1px solid rgba(102, 126, 234, 0.2);
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                margin: 1rem 0;
            ">
                <div style="
                    display: inline-block;
                    width: 50px;
                    height: 50px;
                    border: 3px solid rgba(102, 126, 234, 0.2);
                    border-top: 3px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 1rem;
                "></div>
                <div style="color: #ffffff; font-weight: 500; margin-bottom: 0.5rem;">
                    🤖 Elaborazione in corso...
                </div>
                <div style="
                    display: flex;
                    justify-content: center;
                    gap: 2rem;
                    margin-top: 1rem;
                ">
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: #6c6c7c; text-transform: uppercase;">Step 1</div>
                        <div style="font-size: 0.85rem; color: #a0a0b0;">Analisi NL</div>
                    </div>
                    <div style="color: #667eea;">→</div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: #6c6c7c; text-transform: uppercase;">Step 2</div>
                        <div style="font-size: 0.85rem; color: #a0a0b0;">Gen. SQL</div>
                    </div>
                    <div style="color: #667eea;">→</div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: #6c6c7c; text-transform: uppercase;">Step 3</div>
                        <div style="font-size: 0.85rem; color: #a0a0b0;">Esecuzione</div>
                    </div>
                </div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
            """, unsafe_allow_html=True)
        
        # Esegui la query
        import time
        start_time = time.time()
        result = call_backend(question)
        query_time = time.time() - start_time
        
        # Rimuovi il loading
        loading_placeholder.empty()
        
        if result["success"]:
            data = result["data"]
            generated_sql = data.get("generated_sql", "N/A")
            query_results = data.get("data", [])
            
            # Salva in session state
            st.session_state.current_sql = generated_sql
            st.session_state.current_df = pd.DataFrame(query_results) if query_results else pd.DataFrame()
            st.session_state.current_results = query_results
            st.session_state.last_query_time = query_time
            
            # Aggiungi alla cronologia
            add_to_history(question, generated_sql, True)
            
            # Success notification premium
            stats = calculate_query_stats(st.session_state.current_df)
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(0, 212, 170, 0.1) 0%, rgba(102, 126, 234, 0.05) 100%);
                border: 1px solid rgba(0, 212, 170, 0.3);
                border-radius: 12px;
                padding: 1rem 1.5rem;
                margin: 1rem 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="
                            width: 40px;
                            height: 40px;
                            background: linear-gradient(135deg, #00d4aa, #667eea);
                            border-radius: 10px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.2rem;
                        ">✓</div>
                        <div>
                            <div style="color: #00d4aa; font-weight: 600;">Query completata</div>
                            <div style="color: #a0a0b0; font-size: 0.8rem;">
                                {stats['rows']} righe • {stats['cols']} colonne • {query_time:.2f}s
                            </div>
                        </div>
                    </div>
                    <div style="
                        background: rgba(0, 212, 170, 0.15);
                        border-radius: 20px;
                        padding: 0.25rem 0.75rem;
                        font-size: 0.75rem;
                        color: #00d4aa;
                    ">⚡ {stats['memory']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.session_state.last_query_time = query_time
            add_to_history(question, "ERRORE", False)
            
            # Error notification premium
            st.markdown(f"""
            <div style="
                background: rgba(255, 107, 107, 0.1);
                border: 1px solid rgba(255, 107, 107, 0.3);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
            ">
                <div style="display: flex; align-items: flex-start; gap: 1rem;">
                    <div style="
                        width: 40px;
                        height: 40px;
                        background: rgba(255, 107, 107, 0.2);
                        border-radius: 10px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 1.2rem;
                        flex-shrink: 0;
                    ">❌</div>
                    <div style="flex: 1;">
                        <div style="color: #ff6b6b; font-weight: 600; margin-bottom: 0.5rem;">Errore nell'esecuzione</div>
                        <div style="color: #a0a0b0; font-size: 0.9rem; margin-bottom: 1rem;">{result['error']}</div>
                        
                        <div style="
                            background: rgba(0, 0, 0, 0.2);
                            border-radius: 8px;
                            padding: 1rem;
                        ">
                            <div style="color: #ffffff; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.5rem;">
                                💡 Possibili soluzioni:
                            </div>
                            <ul style="color: #a0a0b0; font-size: 0.8rem; margin: 0; padding-left: 1.25rem; line-height: 1.6;">
                                <li>Verifica che il backend sia attivo su porta 8000</li>
                                <li>Prova a riformulare la domanda in modo più semplice</li>
                                <li>Controlla i nomi delle tabelle (customers, products, orders)</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# SEZIONE RISULTATI - PREMIUM LAYOUT
# ============================================================================

if st.session_state.current_sql:
    # Separator elegante
    st.markdown("""
    <div style="
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
        margin: 2rem 0;
    "></div>
    """, unsafe_allow_html=True)
    
    # Layout a due colonne con card glass morphism
    col_sql, col_viz = st.columns([1, 2])
    
    with col_sql:
        # SQL Card Premium
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(13, 17, 23, 0.8) 0%, rgba(22, 27, 34, 0.8) 100%);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 16px;
            overflow: hidden;
        ">
            <!-- Header -->
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.75rem 1rem;
                background: rgba(102, 126, 234, 0.1);
                border-bottom: 1px solid rgba(102, 126, 234, 0.2);
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div style="
                        width: 28px;
                        height: 28px;
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        border-radius: 6px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 0.8rem;
                    ">🔧</div>
                    <span style="font-weight: 600; color: #ffffff; font-size: 0.9rem;">SQL Generato</span>
                </div>
                <span style="
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    font-size: 0.6rem;
                    font-weight: 600;
                    padding: 3px 8px;
                    border-radius: 4px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                ">SQL</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # SQL Code con syntax highlighting
        st.code(st.session_state.current_sql, language="sql")
        
        # Copy button
        if st.button("📋 Copia SQL", use_container_width=True, key="copy_sql"):
            st.toast("✅ SQL copiato negli appunti!", icon="📋")
        
        # Info Dataset Card - Collapsible
        if st.session_state.current_df is not None and not st.session_state.current_df.empty:
            df = st.session_state.current_df
            
            with st.expander("📊 Statistiche Dataset", expanded=True):
                # Metrics grid
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                with stat_col1:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #667eea;">{len(df):,}</div>
                        <div style="font-size: 0.7rem; color: #6c6c7c; text-transform: uppercase;">Righe</div>
                    </div>
                    """, unsafe_allow_html=True)
                with stat_col2:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #764ba2;">{len(df.columns)}</div>
                        <div style="font-size: 0.7rem; color: #6c6c7c; text-transform: uppercase;">Colonne</div>
                    </div>
                    """, unsafe_allow_html=True)
                with stat_col3:
                    numeric_count = len(df.select_dtypes(include=['number']).columns)
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #00d4aa;">{numeric_count}</div>
                        <div style="font-size: 0.7rem; color: #6c6c7c; text-transform: uppercase;">Numeriche</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Schema colonne
                st.markdown("""
                <div style="
                    font-size: 0.7rem;
                    color: #6c6c7c;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    margin: 0.75rem 0 0.5rem 0;
                ">Schema Colonne</div>
                """, unsafe_allow_html=True)
                
                # Chips per le colonne
                cols_html = ""
                for col in df.columns:
                    dtype = df[col].dtype
                    if 'int' in str(dtype) or 'float' in str(dtype):
                        color = "#667eea"
                        icon = "🔢"
                    elif 'date' in str(dtype).lower() or 'time' in str(dtype).lower():
                        color = "#00d4aa"
                        icon = "📅"
                    else:
                        color = "#764ba2"
                        icon = "📝"
                    
                    cols_html += f"""
                    <span style="
                        background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15);
                        border: 1px solid {color}40;
                        color: {color};
                        padding: 3px 8px;
                        border-radius: 12px;
                        font-size: 0.7rem;
                        margin: 2px;
                        display: inline-block;
                    ">{icon} {col}</span>
                    """
                
                st.markdown(f"""
                <div style="line-height: 2;">
                    {cols_html}
                </div>
                """, unsafe_allow_html=True)
    
    with col_viz:
        # Visualization Card
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 1.25rem;
        ">
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 1rem;
                padding-bottom: 0.75rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div style="
                        width: 32px;
                        height: 32px;
                        background: linear-gradient(135deg, #00d4aa, #667eea);
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 0.9rem;
                    ">📈</div>
                    <span style="font-weight: 600; color: #ffffff;">Visualizzazione</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.current_df is not None and not st.session_state.current_df.empty:
            df = st.session_state.current_df
            
            # Rileva tipo di grafico automaticamente
            chart_type = detect_chart_type(df, st.session_state.current_sql)
            
            # Toggle per scegliere visualizzazione - styled as pills
            viz_options = ["🔮 Auto", "📋 Tabella", "📊 Barre", "🥧 Torta", "📈 Linea", "🌊 Area", "⚬ Scatter"]
            selected_viz = st.radio(
                "Tipo visualizzazione:",
                viz_options,
                horizontal=True,
                key="viz_selector",
                label_visibility="collapsed"
            )
            
            # Mappa selezione a tipo
            viz_map = {
                "🔮 Auto": chart_type,
                "📋 Tabella": "table",
                "📊 Barre": "bar",
                "🥧 Torta": "pie",
                "📈 Linea": "line",
                "🌊 Area": "area",
                "⚬ Scatter": "scatter"
            }
            
            final_chart_type = viz_map.get(selected_viz, "table")
            
            # Container per il grafico
            st.markdown("""
            <div style="
                background: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
            ">
            """, unsafe_allow_html=True)
            
            # Crea visualizzazione
            create_visualization(df, final_chart_type, st.session_state.current_sql)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            # Empty state elegante
            st.markdown("""
            <div style="
                background: rgba(102, 126, 234, 0.05);
                border: 1px dashed rgba(102, 126, 234, 0.2);
                border-radius: 12px;
                padding: 3rem;
                text-align: center;
                margin-top: 1rem;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;">📭</div>
                <p style="color: #6c6c7c; margin: 0;">Nessun dato restituito dalla query</p>
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# FOOTER PREMIUM
# ============================================================================

st.markdown("---")
st.markdown("""
<div class="premium-footer">
    <p>📊 <span class="brand">DataPulse</span> — AI-Powered Business Intelligence</p>
    <div class="tech-badges">
        <span class="tech-badge">⚡ FastAPI</span>
        <span class="tech-badge">🗄️ SQLite</span>
        <span class="tech-badge">🤖 Google Gemini</span>
        <span class="tech-badge">🎨 Streamlit</span>
        <span class="tech-badge">📈 Plotly</span>
    </div>
    <p style="margin-top: 1rem; font-size: 0.75rem;">Made with ❤️ for data-driven decisions</p>
</div>
""", unsafe_allow_html=True)