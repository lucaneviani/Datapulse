"""
DataPulse Frontend

Streamlit-based web interface for AI-powered data analytics.
Features a professional dark theme with support for custom database uploads
and multi-language localization.

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
import sys
import os
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.i18n import i18n, t, set_language, get_language, get_supported_languages, SUPPORTED_LANGUAGES

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="DataPulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

BACKEND_URL = "http://127.0.0.1:8000"
API_ENDPOINT = f"{BACKEND_URL}/api/analyze"

# -----------------------------------------------------------------------------
# Custom CSS
# -----------------------------------------------------------------------------

st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* D9: Theme Variables - Dark Mode (default) */
    :root, [data-theme="dark"] {
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
    
    /* D9: Light Mode Theme */
    [data-theme="light"] {
        --bg-primary: #f8fafc;
        --bg-secondary: #ffffff;
        --bg-card: #ffffff;
        --bg-hover: #f1f5f9;
        --border-color: #e2e8f0;
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --accent-blue: #2563eb;
        --accent-purple: #7c3aed;
        --accent-green: #059669;
        --accent-red: #dc2626;
        --accent-yellow: #d97706;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--bg-primary);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit elements - keep sidebar toggle visible */
    #MainMenu, footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Hide header text but keep sidebar toggle button */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Sidebar toggle button styling */
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="collapsedControl"] {
        visibility: visible !important;
        display: block !important;
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        position: fixed !important;
        top: 14px !important;
        left: 14px !important;
        z-index: 999999 !important;
        padding: 8px !important;
        cursor: pointer !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2) !important;
    }
    
    button[data-testid="stSidebarCollapseButton"]:hover,
    button[data-testid="collapsedControl"]:hover {
        background-color: var(--bg-hover) !important;
        border-color: var(--accent-blue) !important;
    }
    
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
    
    /* D3: Mobile Responsiveness */
    @media (max-width: 768px) {
        .metric-value { font-size: 32px !important; }
        .metric-container { padding: 20px !important; }
        .stTabs [data-baseweb="tab"] { padding: 6px 10px !important; font-size: 13px !important; }
        h1 { font-size: 28px !important; }
        .history-item { padding: 8px 10px !important; }
    }
    
    @media (max-width: 480px) {
        .metric-value { font-size: 24px !important; }
        .stButton > button { padding: 10px 16px !important; font-size: 13px !important; }
    }
    
    /* D8: Accessibility - Focus states */
    .stButton > button:focus,
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {
        outline: 2px solid var(--accent-blue) !important;
        outline-offset: 2px !important;
    }
    
    /* D8: High contrast for better readability */
    .stMarkdown p { color: #d1d5db !important; }
    
    /* D8: Skip link for keyboard navigation */
    .skip-link {
        position: absolute;
        top: -40px;
        left: 0;
        background: var(--accent-blue);
        color: white;
        padding: 8px 16px;
        z-index: 100;
        transition: top 0.3s;
    }
    .skip-link:focus { top: 0; }
    
    /* =========== ENHANCED UI/UX =========== */
    
    /* Micro-animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.3s ease-out forwards;
    }
    
    .animate-slide-in {
        animation: slideIn 0.3s ease-out forwards;
    }
    
    /* Skeleton loading */
    .skeleton {
        background: linear-gradient(90deg, var(--bg-card) 0%, var(--bg-hover) 50%, var(--bg-card) 100%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 8px;
    }
    
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    .skeleton-text {
        height: 16px;
        margin-bottom: 8px;
    }
    
    .skeleton-title {
        height: 24px;
        width: 60%;
        margin-bottom: 16px;
    }
    
    .skeleton-card {
        height: 120px;
        margin-bottom: 16px;
    }
    
    /* Toast notifications */
    .toast {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        border-radius: 12px;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    
    .toast-success {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
    }
    
    .toast-error {
        background: linear-gradient(135deg, #dc2626, #ef4444);
        color: white;
    }
    
    .toast-info {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
        color: white;
    }
    
    /* Enhanced buttons */
    .btn-primary {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px 28px !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
    }
    
    .btn-secondary {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    .btn-secondary:hover {
        background: var(--bg-hover) !important;
        border-color: var(--accent-blue) !important;
    }
    
    .btn-danger {
        background: linear-gradient(135deg, #dc2626, #ef4444) !important;
        border: none !important;
        color: white !important;
    }
    
    /* Enhanced cards */
    .card-elevated {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .card-elevated:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        border-color: var(--accent-blue);
    }
    
    /* Feature highlight */
    .feature-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15));
        color: var(--accent-blue);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Stats grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }
    
    .stat-item {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.2s;
    }
    
    .stat-item:hover {
        border-color: var(--accent-blue);
        transform: scale(1.02);
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    
    .stat-label {
        font-size: 12px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* D11: Visual feedback for keyboard shortcuts */
    .keyboard-hint {
        font-size: 11px;
        color: var(--text-muted);
        background: var(--bg-hover);
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
    }
    
    /* D10: Empty State Styles */
    .empty-state {
        text-align: center;
        padding: 48px 24px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(139, 92, 246, 0.05));
        border: 1px dashed var(--border-color);
        border-radius: 16px;
        margin: 24px 0;
    }
    .empty-state-icon {
        font-size: 56px;
        margin-bottom: 16px;
        opacity: 0.8;
    }
    .empty-state-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    .empty-state-description {
        font-size: 14px;
        color: var(--text-muted);
        max-width: 400px;
        margin: 0 auto 20px;
        line-height: 1.6;
    }
    .empty-state-cta {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
        text-decoration: none;
        cursor: pointer;
    }
    
    /* D12: Autocomplete Dropdown */
    .autocomplete-container {
        position: relative;
    }
    .autocomplete-dropdown {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 1000;
        max-height: 300px;
        overflow-y: auto;
    }
    .autocomplete-item {
        padding: 10px 14px;
        cursor: pointer;
        border-bottom: 1px solid var(--border-color);
        transition: background 0.15s;
    }
    .autocomplete-item:hover {
        background: var(--bg-hover);
    }
    .autocomplete-item:last-child {
        border-bottom: none;
    }
    .autocomplete-text {
        color: var(--text-primary);
        font-size: 14px;
    }
    .autocomplete-hint {
        color: var(--text-muted);
        font-size: 11px;
        margin-top: 2px;
    }
    
    /* D9: Theme Toggle Button */
    .theme-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .theme-toggle:hover {
        background: var(--bg-hover);
    }
    
    /* =========== HERO SECTION =========== */
    .hero-section {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
        border-radius: 20px;
        padding: 48px 32px;
        text-align: center;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.05) 0%, transparent 70%);
        animation: rotateBackground 20s linear infinite;
    }
    
    @keyframes rotateBackground {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .hero-title {
        font-size: 48px;
        font-weight: 800;
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 16px;
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        font-size: 18px;
        color: var(--text-muted);
        max-width: 600px;
        margin: 0 auto 24px;
        position: relative;
        z-index: 1;
    }
    
    /* =========== PROGRESS INDICATOR =========== */
    .progress-container {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .progress-bar {
        height: 8px;
        background: var(--bg-hover);
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 8px;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    
    .progress-text {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: var(--text-muted);
    }
    
    /* =========== ENHANCED DATA TABLES =========== */
    .dataframe {
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, var(--bg-card), var(--bg-hover)) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        padding: 14px 16px !important;
        text-align: left !important;
        border-bottom: 2px solid var(--accent-blue) !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
    }
    
    .dataframe td {
        padding: 12px 16px !important;
        border-bottom: 1px solid var(--border-color) !important;
        transition: background 0.15s !important;
    }
    
    .dataframe tr:hover td {
        background: var(--bg-hover) !important;
    }
    
    .dataframe tr:last-child td {
        border-bottom: none !important;
    }
    
    /* =========== TOOLTIP =========== */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltip-text {
        visibility: hidden;
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(17, 24, 39, 0.95);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.2s, visibility 0.2s;
    }
    
    .tooltip:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    
    /* =========== CODE BLOCK STYLING =========== */
    .code-block {
        background: #1e1e2e;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 13px;
        line-height: 1.6;
        overflow-x: auto;
        position: relative;
    }
    
    .code-block::before {
        content: 'SQL';
        position: absolute;
        top: 8px;
        right: 12px;
        font-size: 10px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .code-keyword { color: #ff79c6; }
    .code-string { color: #f1fa8c; }
    .code-number { color: #bd93f9; }
    .code-function { color: #50fa7b; }
    .code-comment { color: #6272a4; font-style: italic; }
    
    /* =========== CHIP / TAG STYLING =========== */
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 500;
        margin: 2px;
    }
    
    .chip-primary {
        background: rgba(59, 130, 246, 0.15);
        color: var(--accent-blue);
    }
    
    .chip-success {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }
    
    .chip-warning {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
    }
    
    .chip-danger {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }
    
    /* =========== LOADING SPINNER =========== */
    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid var(--border-color);
        border-top-color: var(--accent-blue);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .loading-text {
        text-align: center;
        color: var(--text-muted);
        font-size: 14px;
        margin-top: 12px;
    }
    
    /* =========== NOTIFICATION BADGE =========== */
    .notification-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        background: linear-gradient(135deg, #ef4444, #f97316);
        color: white;
        font-size: 10px;
        font-weight: 700;
        min-width: 18px;
        height: 18px;
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 5px;
    }
    
    /* =========== DIVIDER =========== */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 24px 0;
    }
    
    .divider-text {
        display: flex;
        align-items: center;
        gap: 16px;
        color: var(--text-muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .divider-text::before,
    .divider-text::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border-color);
    }
</style>
""", unsafe_allow_html=True)

# D9: Apply theme dynamically
def apply_theme():
    """Apply current theme to the page via JavaScript."""
    theme = st.session_state.get("theme", "dark")
    st.markdown(f"""
    <script>
        document.documentElement.setAttribute('data-theme', '{theme}');
        document.body.setAttribute('data-theme', '{theme}');
        // Also update Streamlit's root element
        const stApp = document.querySelector('.stApp');
        if (stApp) stApp.setAttribute('data-theme', '{theme}');
    </script>
    """, unsafe_allow_html=True)

apply_theme()

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------

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
# Session management for custom databases
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "db_type" not in st.session_state:
    st.session_state.db_type = "demo"
if "db_tables" not in st.session_state:
    st.session_state.db_tables = []
if "db_schema" not in st.session_state:
    st.session_state.db_schema = ""
# Authentication state
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user" not in st.session_state:
    st.session_state.user = None
# D9: Theme state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
# D12: Query suggestions cache
if "query_suggestions" not in st.session_state:
    st.session_state.query_suggestions = []
if "saved_queries" not in st.session_state:
    st.session_state.saved_queries = []
if "show_auth_modal" not in st.session_state:
    st.session_state.show_auth_modal = False
# Language state
if "language" not in st.session_state:
    st.session_state.language = "it"
# Apply saved language
set_language(st.session_state.language)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def check_backend_health():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False


def create_session():
    """Create a new session with the backend."""
    try:
        response = requests.post(f"{BACKEND_URL}/api/session/create", timeout=5)
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data["session_id"]
            st.session_state.db_type = data["db_type"]
            st.session_state.db_tables = data["tables"]
            return True
    except:
        pass
    return False


def send_query(question: str) -> dict:
    """Send query to backend API."""
    try:
        # Use session endpoint if session exists
        if st.session_state.session_id:
            url = f"{BACKEND_URL}/api/session/{st.session_state.session_id}/analyze"
        else:
            url = API_ENDPOINT
        
        response = requests.post(
            url,
            json={"question": question},
            timeout=30
        )
        
        # D6: Handle session expiry gracefully
        if response.status_code == 404:
            error_detail = response.json().get("detail", "")
            if "session" in error_detail.lower() or "not found" in error_detail.lower():
                # Session expired - try to recreate
                st.session_state.session_id = None
                if create_session():
                    # Retry with new session
                    new_url = f"{BACKEND_URL}/api/session/{st.session_state.session_id}/analyze"
                    response = requests.post(new_url, json={"question": question}, timeout=30)
                    return response.json()
                else:
                    return {"error": "Sessione scaduta. Ricarica la pagina per continuare."}
        
        if response.status_code == 422:
            # Validation error
            detail = response.json().get("detail", [])
            if isinstance(detail, list) and detail:
                msg = detail[0].get("msg", "Errore di validazione")
            else:
                msg = str(detail)
            return {"error": f"Validazione fallita: {msg}"}
        
        if response.status_code >= 500:
            return {"error": "Errore interno del server. Riprova tra qualche istante."}
        
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Impossibile connettersi al backend. Verifica che il server sia in esecuzione."}
    except requests.exceptions.Timeout:
        return {"error": "Timeout: la richiesta sta impiegando troppo tempo. Prova una domanda più semplice."}
    except requests.exceptions.JSONDecodeError:
        return {"error": "Errore nel parsing della risposta dal server."}
    except Exception as e:
        return {"error": f"Errore inatteso: {str(e)}"}


def upload_files_to_backend(files, file_type="csv"):
    """Upload files to backend and create custom database."""
    if not st.session_state.session_id:
        if not create_session():
            return False, "Impossibile creare la sessione"
    
    try:
        if file_type == "csv":
            url = f"{BACKEND_URL}/api/session/{st.session_state.session_id}/upload/csv"
            files_data = [("files", (f.name, f.getvalue(), "text/csv")) for f in files]
        else:  # sqlite
            url = f"{BACKEND_URL}/api/session/{st.session_state.session_id}/upload/sqlite"
            f = files[0]
            files_data = {"file": (f.name, f.getvalue(), "application/octet-stream")}
        
        response = requests.post(url, files=files_data, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.db_type = data["db_type"]
            st.session_state.db_tables = data["tables"]
            st.session_state.db_schema = data.get("schema", "")
            return True, data["message"]
        else:
            error_msg = response.json().get("detail", "Errore sconosciuto")
            return False, error_msg
            
    except Exception as e:
        return False, f"Errore upload: {str(e)}"


def reset_to_demo():
    """Reset session to demo database."""
    if not st.session_state.session_id:
        return True, "Già in modalità demo"
    
    try:
        url = f"{BACKEND_URL}/api/session/{st.session_state.session_id}/reset"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.db_type = data["db_type"]
            st.session_state.db_tables = data["tables"]
            st.session_state.db_schema = ""
            return True, data["message"]
        else:
            return False, "Errore nel reset"
    except Exception as e:
        return False, f"Errore: {str(e)}"


# -----------------------------------------------------------------------------
# Authentication Functions
# -----------------------------------------------------------------------------

def login_user(username: str, password: str):
    """Login user and get JWT token."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.auth_token = data["token"]
            st.session_state.user = {
                "id": data["user_id"],
                "username": data["username"],
                "email": data["email"]
            }
            # D7: Load history from backend on login
            load_history_from_backend()
            load_saved_queries()
            return True, "Login effettuato con successo"
        else:
            detail = response.json().get("detail", "Credenziali non valide")
            return False, detail
    except Exception as e:
        return False, f"Errore: {str(e)}"


def register_user(username: str, email: str, password: str):
    """Register new user."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json={"username": username, "email": email, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.auth_token = data["token"]
            st.session_state.user = {
                "id": data["user_id"],
                "username": data["username"],
                "email": data["email"]
            }
            # D7: Load history from backend on registration
            load_history_from_backend()
            load_saved_queries()
            return True, "Registrazione completata"
        else:
            detail = response.json().get("detail", "Errore nella registrazione")
            return False, detail
    except Exception as e:
        return False, f"Errore: {str(e)}"


def logout_user():
    """Logout user."""
    if st.session_state.auth_token:
        try:
            requests.post(
                f"{BACKEND_URL}/api/auth/logout",
                headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
                timeout=5
            )
        except:
            pass
    st.session_state.auth_token = None
    st.session_state.user = None


# -----------------------------------------------------------------------------
# Export Functions
# -----------------------------------------------------------------------------

def export_to_format(data: list, format_type: str, title: str = "Report", query: str = None):
    """Export data to specified format."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/export",
            json={
                "data": data,
                "format": format_type,
                "title": title,
                "query": query
            },
            timeout=30
        )
        if response.status_code == 200:
            return True, response.content
        else:
            return False, response.json().get("detail", "Errore export")
    except Exception as e:
        return False, str(e)


def generate_dashboard(data: list, title: str = "Dashboard"):
    """Generate automatic dashboard."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/dashboard/create",
            json={"data": data, "title": title},
            timeout=30
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Errore generazione dashboard")
    except Exception as e:
        return False, str(e)


# -----------------------------------------------------------------------------
# D7: History Persistence Functions
# -----------------------------------------------------------------------------

def save_history_to_backend():
    """Save query history to backend for logged-in users."""
    if not st.session_state.auth_token or not st.session_state.history:
        return
    try:
        requests.post(
            f"{BACKEND_URL}/api/user/history",
            json={"history": st.session_state.history},
            headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
            timeout=5
        )
    except:
        pass  # Silent fail - history is not critical


def load_history_from_backend():
    """Load query history from backend for logged-in users."""
    if not st.session_state.auth_token:
        return
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/user/history",
            headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.history = data.get("history", [])[:10]
    except:
        pass


def load_saved_queries():
    """Load saved/favorite queries for logged-in users."""
    if not st.session_state.auth_token:
        return []
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/user/queries",
            headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("queries", [])
    except:
        pass
    return []


def save_query_to_favorites(question: str, sql: str):
    """Save a query to user's favorites."""
    if not st.session_state.auth_token:
        return False, "Effettua il login per salvare le query"
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/user/queries",
            json={"question": question, "sql": sql},
            headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
            timeout=5
        )
        if response.status_code == 200:
            return True, "Query salvata!"
        return False, response.json().get("detail", "Errore")
    except Exception as e:
        return False, str(e)


# -----------------------------------------------------------------------------
# D12: Query Autocomplete Functions
# -----------------------------------------------------------------------------

def get_query_suggestions(partial_query: str, db_tables: list) -> list:
    """Generate query suggestions based on input and schema."""
    suggestions = []
    partial_lower = partial_query.lower().strip()
    
    if not partial_lower:
        return []
    
    # Common query patterns
    patterns = [
        ("quanti", "Quanti {table} ci sono?", "COUNT query"),
        ("mostra", "Mostra i primi 10 {table}", "SELECT TOP query"),
        ("totale", "Qual è il totale di {field}?", "SUM query"),
        ("media", "Qual è la media di {field}?", "AVG query"),
        ("massimo", "Qual è il massimo {field}?", "MAX query"),
        ("minimo", "Qual è il minimo {field}?", "MIN query"),
        ("raggruppa", "Raggruppa {table} per {field}", "GROUP BY query"),
        ("ordina", "Ordina {table} per {field}", "ORDER BY query"),
        ("filtra", "Filtra {table} dove {field} = ", "WHERE query"),
        ("top", "Top 5 {table} per {field}", "TOP N query"),
    ]
    
    # Match based on input
    for keyword, template, description in patterns:
        if keyword.startswith(partial_lower[:3]) or partial_lower.startswith(keyword[:3]):
            for table in (db_tables or ["customers", "orders", "products"]):
                suggestion = template.replace("{table}", table).replace("{field}", "valore")
                suggestions.append({
                    "text": suggestion,
                    "description": description,
                    "type": "pattern"
                })
    
    # Add from history
    for item in st.session_state.history[:5]:
        if partial_lower in item.get("question", "").lower():
            suggestions.append({
                "text": item["question"],
                "description": "Query recente",
                "type": "history"
            })
    
    # Add saved queries
    for saved in st.session_state.saved_queries[:5]:
        if partial_lower in saved.get("question", "").lower():
            suggestions.append({
                "text": saved["question"],
                "description": "Query salvata ⭐",
                "type": "saved"
            })
    
    # Remove duplicates and limit
    seen = set()
    unique = []
    for s in suggestions:
        if s["text"] not in seen:
            seen.add(s["text"])
            unique.append(s)
    
    return unique[:8]


def add_to_history(question: str, success: bool):
    """Add query to history."""
    entry = {
        "time": datetime.now().strftime("%H:%M"),
        "question": question[:50] + "..." if len(question) > 50 else question,
        "full_question": question,
        "success": success
    }
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:10]
    
    # D7: Persist to backend if logged in
    save_history_to_backend()


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
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'displaylogo': False,
            'toImageButtonOptions': {'format': 'png', 'filename': 'datapulse_chart'}
        })
        
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
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
            'toImageButtonOptions': {'format': 'png', 'filename': 'datapulse_chart'}
        })
        
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
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'displaylogo': False
        })
        
    elif chart_type == "scatter" and len(numeric_cols) >= 2:
        fig = go.Figure(go.Scatter(
            x=df[numeric_cols[0]],
            y=df[numeric_cols[1]],
            mode='markers',
            marker=dict(size=10, color='#3b82f6', line=dict(color='#0a0a0b', width=1))
        ))
        fig.update_layout(**layout, height=400, xaxis_title=numeric_cols[0], yaxis_title=numeric_cols[1])
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d'],
            'displaylogo': False
        })
        
    else:
        st.dataframe(df, use_container_width=True, height=400)


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

with st.sidebar:
    # Language Selector at top
    lang_options = {code: f"{info['flag']} {info['native']}" for code, info in SUPPORTED_LANGUAGES.items()}
    col_lang, col_theme = st.columns([3, 1])
    
    with col_lang:
        selected_lang = st.selectbox(
            "🌐",
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(st.session_state.language),
            key="lang_selector",
            label_visibility="collapsed"
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            set_language(selected_lang)
            st.rerun()
    
    # D9: Theme Toggle
    with col_theme:
        theme_icon = "🌙" if st.session_state.theme == "dark" else "☀️"
        if st.button(theme_icon, key="theme_toggle", help="Cambia tema"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    
    # Logo & Brand
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; padding: 16px 0; border-bottom: 1px solid #2a2a32; margin-bottom: 24px;">
            <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px;">⚡</div>
            <div>
                <div style="font-size: 18px; font-weight: 700; color: var(--text-primary);">{t('app_name')}</div>
                <div style="font-size: 12px; color: var(--text-muted);">{t('app_tagline')}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # Authentication Section
    # -------------------------------------------------------------------------
    
    if st.session_state.user:
        # User logged in
        st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; padding: 12px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #10b981, #3b82f6); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;">
                        {st.session_state.user['username'][0].upper()}
                    </div>
                    <div>
                        <div style="color: #ffffff; font-weight: 500; font-size: 14px;">{st.session_state.user['username']}</div>
                        <div style="color: #6b7280; font-size: 11px;">{st.session_state.user['email']}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🚪 {t('auth_logout')}", use_container_width=True, key="logout_btn"):
            logout_user()
            st.rerun()
    else:
        # Auth tabs
        auth_tab1, auth_tab2 = st.tabs([f"🔐 {t('auth_login')}", f"📝 {t('auth_register')}"])
        
        with auth_tab1:
            login_username = st.text_input(t('auth_username'), key="login_user", placeholder=t('auth_username'))
            login_password = st.text_input(t('auth_password'), type="password", key="login_pass", placeholder=t('auth_password'))
            
            if st.button(t('auth_login_btn'), use_container_width=True, key="login_submit"):
                if login_username and login_password:
                    with st.spinner(t('auth_logging_in')):
                        success, message = login_user(login_username, login_password)
                    if success:
                        st.success("✅ " + t('auth_login_success'))
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ " + message)
                else:
                    st.warning(t('auth_fill_all'))
        
        with auth_tab2:
            reg_username = st.text_input(t('auth_username'), key="reg_user", placeholder=t('auth_username'))
            reg_email = st.text_input(t('auth_email'), key="reg_email", placeholder=t('auth_email'))
            reg_password = st.text_input(t('auth_password'), type="password", key="reg_pass", placeholder=t('auth_password_hint'))
            
            if st.button(t('auth_register_btn'), use_container_width=True, key="register_submit"):
                if reg_username and reg_email and reg_password:
                    if len(reg_password) < 6:
                        st.warning(t('auth_password_short'))
                    else:
                        with st.spinner(t('auth_registering')):
                            success, message = register_user(reg_username, reg_email, reg_password)
                        if success:
                            st.success("✅ " + t('auth_register_success'))
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ " + message)
                else:
                    st.warning(t('auth_fill_all'))
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # System Status
    is_online = check_backend_health()
    status_html = f"""
        <div class="status-success">
            <span>●</span> {t('status_online')}
        </div>
    """ if is_online else f"""
        <div class="status-error">
            <span>●</span> {t('status_offline')}
        </div>
    """
    st.markdown(status_html, unsafe_allow_html=True)
    
    # Database Status
    db_type = st.session_state.db_type
    if db_type == "custom":
        st.markdown(f"""
            <div style="margin-top: 8px; background: rgba(139, 92, 246, 0.15); color: #8b5cf6; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; display: inline-block;">
                📊 {t('status_custom_db')}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="margin-top: 8px; background: rgba(59, 130, 246, 0.15); color: #3b82f6; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; display: inline-block;">
                📁 {t('status_demo_db')}
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # Data Upload Section
    # -------------------------------------------------------------------------
    
    st.markdown(f"#### 📤 {t('upload_title')}")
    
    # Initialize session if needed
    if is_online and not st.session_state.session_id:
        create_session()
    
    upload_tab1, upload_tab2 = st.tabs([t('upload_csv_tab'), t('upload_sqlite_tab')])
    
    with upload_tab1:
        st.caption(t('upload_csv_hint'))
        csv_files = st.file_uploader(
            t('upload_select_files'),
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key="csv_uploader",
            label_visibility="collapsed"
        )
        
        if csv_files:
            st.caption(f"📁 {len(csv_files)} {t('upload_files_selected')}")
            if st.button(f"📤 {t('upload_btn_csv')}", use_container_width=True, key="upload_csv_btn"):
                with st.spinner(t('upload_loading')):
                    success, message = upload_files_to_backend(csv_files, "csv")
                
                if success:
                    st.success(f"✅ {t('upload_success')}")
                    # Clear previous results
                    st.session_state.last_result = None
                    st.session_state.last_df = None
                    st.session_state.last_sql = None
                    st.session_state.history = []
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    with upload_tab2:
        st.caption(t('upload_sqlite_hint'))
        sqlite_file = st.file_uploader(
            t('upload_select_files'),
            type=["db", "sqlite", "sqlite3"],
            accept_multiple_files=False,
            key="sqlite_uploader",
            label_visibility="collapsed"
        )
        
        if sqlite_file:
            st.caption(f"📁 {sqlite_file.name}")
            if st.button(f"📤 {t('upload_btn_sqlite')}", use_container_width=True, key="upload_sqlite_btn"):
                with st.spinner(t('upload_loading')):
                    success, message = upload_files_to_backend([sqlite_file], "sqlite")
                
                if success:
                    st.success(f"✅ {t('upload_success')}")
                    # Clear previous results
                    st.session_state.last_result = None
                    st.session_state.last_df = None
                    st.session_state.last_sql = None
                    st.session_state.history = []
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    # Reset to demo button
    if st.session_state.db_type == "custom":
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"🔄 {t('upload_reset')}", use_container_width=True, key="reset_demo_btn"):
            with st.spinner(t('upload_resetting')):
                success, message = reset_to_demo()
            
            if success:
                st.success(f"✅ {t('upload_reset_success')}")
                st.session_state.last_result = None
                st.session_state.last_df = None
                st.session_state.last_sql = None
                st.session_state.history = []
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # History Section
    st.markdown(f"#### 📋 {t('history_title')}")
    
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
        if st.button(f"🗑️ {t('history_clear')}", use_container_width=True):
            st.session_state.history = []
            st.session_state.last_result = None
            st.session_state.last_sql = None
            st.session_state.last_df = None
            st.rerun()
    else:
        # D10: Improved Empty State for History
        empty_title = t('history_empty') if t('history_empty') else 'Nessuna query ancora'
        empty_desc = 'Fai la tua prima domanda sui dati e apparirà qui la cronologia delle tue ricerche.'
        st.markdown(f"""
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <div class="empty-state-title">{empty_title}</div>
                <div class="empty-state-description">
                    {empty_desc}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Export Section - Advanced
    st.markdown(f"#### 📥 {t('export_title')}")
    
    if st.session_state.last_df is not None and not st.session_state.last_df.empty:
        export_format = st.selectbox(
            t('export_format'),
            ["CSV", "Excel", "PDF", "HTML"],
            key="export_format",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        
        # Quick CSV/JSON export
        with col1:
            csv = st.session_state.last_df.to_csv(index=False)
            st.download_button("📄 CSV", csv, "export.csv", "text/csv", use_container_width=True)
        with col2:
            json_data = st.session_state.last_df.to_json(orient="records", indent=2)
            st.download_button("📋 JSON", json_data, "export.json", "application/json", use_container_width=True)
        
        # Advanced export button
        if st.button(f"📊 {t('export_btn')} {export_format}", use_container_width=True, key="advanced_export"):
            with st.spinner(f"{t('export_generating')} {export_format}..."):
                data_list = st.session_state.last_df.to_dict(orient="records")
                success, result = export_to_format(
                    data=data_list,
                    format_type=export_format.lower(),
                    title="Report DataPulse",
                    query=st.session_state.last_sql
                )
            
            if success:
                ext_map = {"csv": "csv", "excel": "xlsx", "pdf": "pdf", "html": "html"}
                mime_map = {
                    "csv": "text/csv",
                    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "pdf": "application/pdf",
                    "html": "text/html"
                }
                fmt = export_format.lower()
                st.download_button(
                    f"⬇️ {t('export_download')} {export_format}",
                    result,
                    f"report.{ext_map[fmt]}",
                    mime_map[fmt],
                    use_container_width=True,
                    key="download_advanced"
                )
            else:
                st.error(f"❌ {t('export_error')}: {result}")
    else:
        st.caption(t('export_run_query'))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Database Schema
    with st.expander(f"📊 {t('schema_title')}"):
        if st.session_state.db_type == "custom" and st.session_state.db_schema:
            st.markdown(f"**📊 {t('schema_custom')}**")
            st.code(st.session_state.db_schema, language=None)
        else:
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
        
        if st.session_state.db_tables:
            st.markdown("---")
            st.markdown(f"**{t('schema_tables')}:** {', '.join(st.session_state.db_tables)}")

# -----------------------------------------------------------------------------
# Main Content
# -----------------------------------------------------------------------------

# Hero Section (only when no results)
if st.session_state.last_result is None:
    # Different hero based on database type
    if st.session_state.db_type == "custom":
        hero_subtitle = t('app_description_custom')
    else:
        hero_subtitle = t('app_description')
    
    st.markdown(f"""
        <div style="text-align: center; padding: 60px 20px; margin-bottom: 32px;">
            <h1 style="font-size: 48px; font-weight: 700; margin-bottom: 16px; color: #3b82f6;">
                ⚡ DataPulse
            </h1>
            <p style="font-size: 18px; color: #9ca3af; max-width: 500px; margin: 0 auto; line-height: 1.6;">
                {hero_subtitle}
            </p>
        </div>
    """, unsafe_allow_html=True)

# Query Input Section
st.markdown(f"### 💬 {t('query_title')}")

col1, col2 = st.columns([5, 1])

with col1:
    placeholder_text = t('query_placeholder_custom') if st.session_state.db_type == "custom" else t('query_placeholder')
    question = st.text_input(
        "query",
        placeholder=placeholder_text,
        label_visibility="collapsed"
    )
    # D11: Keyboard Navigation Hint
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 16px; margin-top: 4px;">
            <span class="keyboard-hint">⏎ Enter per inviare</span>
            <span class="keyboard-hint">↑↓ Naviga suggerimenti</span>
        </div>
    """, unsafe_allow_html=True)

with col2:
    submit = st.button(t('query_btn'), type="primary", use_container_width=True)

# D12: Autocomplete Suggestions - Show when typing
if question and len(question) >= 2 and not submit:
    suggestions_list = get_query_suggestions(
        question, 
        st.session_state.get("db_tables", [])
    )
    if suggestions_list:
        st.markdown("""
            <div class="autocomplete-dropdown" style="position: relative; margin-top: 8px;">
        """, unsafe_allow_html=True)
        
        for idx, suggestion in enumerate(suggestions_list[:5]):
            col_sug = st.columns([1])
            with col_sug[0]:
                if st.button(
                    f"🔍 {suggestion}", 
                    key=f"autocomplete_{idx}",
                    use_container_width=True
                ):
                    st.session_state["_pending_query"] = suggestion
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# Quick suggestions (only when no results)
if st.session_state.last_result is None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"##### 💡 {t('suggestions_title')}")
    
    # Different suggestions based on database type
    if st.session_state.db_type == "custom" and st.session_state.db_tables:
        first_table = st.session_state.db_tables[0] if st.session_state.db_tables else "table"
        suggestions = [
            (f"📊 {t('sug_count_records')}", f"Quanti record ci sono in {first_table}?"),
            (f"📋 {t('sug_show_data')}", f"Mostra i primi 10 record di {first_table}"),
            (f"🔍 {t('sug_structure')}", f"Quali colonne ha {first_table}?"),
            (f"📈 {t('sug_statistics')}", f"Mostra le statistiche di {first_table}")
        ]
    else:
        suggestions = [
            (f"📊 {t('sug_total_sales')}", "Qual è il totale delle vendite?"),
            (f"🌍 {t('sug_by_region')}", "Mostra il fatturato per regione"),
            (f"🏆 {t('sug_top_products')}", "Quali sono i 5 prodotti più venduti?"),
            (f"📈 {t('sug_orders')}", "Quanti ordini ci sono in totale?")
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

# -----------------------------------------------------------------------------
# Query Execution
# -----------------------------------------------------------------------------

if submit and question:
    # D5: Enhanced input validation with inline feedback
    validation_error = None
    if not question.strip():
        validation_error = ("empty", t('query_empty'))
    elif len(question.strip()) < 5:
        validation_error = ("short", t('query_too_short'))
    elif len(question) > 500:
        validation_error = ("long", "La domanda è troppo lunga (max 500 caratteri)")
    elif "<script" in question.lower() or "javascript:" in question.lower():
        validation_error = ("security", "Input non valido: contenuto non permesso")
    
    if validation_error:
        error_type, error_msg = validation_error
        st.markdown(f"""
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); 
                        border-radius: 8px; padding: 12px 16px; margin: 8px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">⚠️</span>
                    <div>
                        <div style="color: #f59e0b; font-weight: 500;">{error_msg}</div>
                        <div style="color: #9ca3af; font-size: 12px; margin-top: 4px;">
                            {'Inserisci una domanda valida' if error_type == 'empty' else
                             'Prova con una domanda più specifica, es: "Quanti clienti ci sono?"' if error_type == 'short' else
                             'Semplifica la domanda per ottenere risultati migliori' if error_type == 'long' else
                             'Rimuovi contenuto non valido dalla domanda'}
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # D2: Enhanced loading state with progress indication
        progress_placeholder = st.empty()
        progress_placeholder.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); 
                        border-radius: 8px; padding: 16px; margin: 8px 0; text-align: center;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                    <div class="loading-spinner" style="width: 24px; height: 24px; border: 3px solid #3b82f6; 
                         border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    <div style="color: #3b82f6; font-weight: 500;">⚡ {t('query_analyzing')}</div>
                </div>
                <div style="color: #6b7280; font-size: 12px; margin-top: 8px;">
                    Generazione SQL in corso con AI...
                </div>
            </div>
            <style>
                @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
            </style>
        """, unsafe_allow_html=True)
        
        start_time = time.time()
        result = send_query(question)
        elapsed = time.time() - start_time
        st.session_state.query_time = elapsed
        progress_placeholder.empty()
        
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

# -----------------------------------------------------------------------------
# Results Display
# -----------------------------------------------------------------------------

if st.session_state.last_result is not None:
    result = st.session_state.last_result
    
    st.markdown("---")
    
    if "error" in result:
        # D1: Enhanced error display with categorization and suggestions
        error_msg = result["error"]
        
        # Categorize error and provide helpful suggestions
        if "connett" in error_msg.lower() or "backend" in error_msg.lower() or "timeout" in error_msg.lower():
            error_icon = "🔌"
            error_title = "Errore di Connessione"
            error_suggestion = "Verifica che il server backend sia in esecuzione (uvicorn backend.main:app)"
            error_color = "#f59e0b"  # Warning yellow
        elif "sql" in error_msg.lower() or "syntax" in error_msg.lower() or "query" in error_msg.lower():
            error_icon = "💾"
            error_title = "Errore SQL"
            error_suggestion = "Prova a riformulare la domanda in modo più specifico"
            error_color = "#ef4444"  # Red
        elif "tabella" in error_msg.lower() or "table" in error_msg.lower() or "column" in error_msg.lower():
            error_icon = "📊"
            error_title = "Tabella o Colonna Non Trovata"
            error_suggestion = "Consulta lo schema database nella sidebar per vedere le tabelle disponibili"
            error_color = "#8b5cf6"  # Purple
        elif "permesso" in error_msg.lower() or "permission" in error_msg.lower() or "blocked" in error_msg.lower():
            error_icon = "🔒"
            error_title = "Operazione Non Permessa"
            error_suggestion = "Solo query SELECT sono consentite per motivi di sicurezza"
            error_color = "#ef4444"
        elif "session" in error_msg.lower() or "sessione" in error_msg.lower():
            error_icon = "🔄"
            error_title = "Sessione Scaduta"
            error_suggestion = "La sessione è scaduta. Ricarica la pagina per crearne una nuova."
            error_color = "#f59e0b"
        else:
            error_icon = "❌"
            error_title = t('results_error')
            error_suggestion = "Prova a riformulare la domanda o controlla i log per maggiori dettagli"
            error_color = "#ef4444"
        
        st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid {error_color}40; border-radius: 12px; padding: 20px; margin: 16px 0;">
                <div style="display: flex; align-items: flex-start; gap: 14px;">
                    <div style="width: 42px; height: 42px; background: {error_color}20; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0;">
                        {error_icon}
                    </div>
                    <div style="flex: 1;">
                        <div style="color: {error_color}; font-weight: 600; font-size: 16px; margin-bottom: 6px;">{error_title}</div>
                        <div style="color: #d1d5db; font-size: 14px; line-height: 1.5;">{error_msg}</div>
                        <div style="margin-top: 12px; padding: 10px 14px; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 3px solid {error_color};">
                            <div style="color: #9ca3af; font-size: 12px; display: flex; align-items: center; gap: 6px;">
                                <span>💡</span> <strong>Suggerimento:</strong> {error_suggestion}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.last_sql:
            with st.expander(f"🔍 {t('results_sql_generated')} (debug)"):
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
                        <div style="color: #10b981; font-weight: 600;">{t('results_success')}</div>
                        <div style="color: #6b7280; font-size: 13px;">{len(df)} {t('results_rows')} • {len(df.columns)} {t('results_columns')} • {query_time:.2f}s</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabs for results
        tab_chart, tab_table, tab_sql, tab_dashboard = st.tabs([f"📊 {t('results_tab_chart')}", f"📋 {t('results_tab_table')}", f"💻 {t('results_tab_sql')}", f"📈 {t('results_tab_dashboard')}"])
        
        with tab_chart:
            if not df.empty:
                col_opt, col_viz = st.columns([1, 4])
                
                with col_opt:
                    auto_type = detect_chart_type(df)
                    options = [t('chart_auto'), t('chart_bar'), t('chart_pie'), t('chart_line'), t('chart_scatter'), t('chart_table'), t('chart_metric')]
                    choice = st.selectbox(t('chart_type'), options, index=0)
                    
                    type_map = {
                        t('chart_auto'): auto_type,
                        t('chart_bar'): "bar",
                        t('chart_pie'): "pie",
                        t('chart_line'): "line",
                        t('chart_scatter'): "scatter",
                        t('chart_table'): "table",
                        t('chart_metric'): "metric"
                    }
                    final_type = type_map.get(choice, "table")
                
                with col_viz:
                    create_chart(df, final_type)
            else:
                st.info(t('results_no_data'))
        
        with tab_table:
            if not df.empty:
                st.dataframe(df, use_container_width=True, height=450)
            else:
                st.warning(t('results_no_results'))
        
        with tab_sql:
            st.markdown(f"##### {t('results_sql_generated')}")
            st.code(st.session_state.last_sql, language="sql")
            
            # D12: Save query to favorites
            col_save, col_copy = st.columns(2)
            with col_save:
                if st.session_state.auth_token:
                    if st.button("⭐ Salva ai preferiti", key="save_query_fav", use_container_width=True):
                        if st.session_state.history:
                            latest_query = st.session_state.history[0].get("full_question", "")
                            save_query_to_favorites(latest_query)
                            st.success("Query salvata ai preferiti!")
                else:
                    st.info("🔐 Accedi per salvare query ai preferiti")
            with col_copy:
                st.markdown(f"<small style='color: var(--text-muted);'>Copia la query SQL per usarla altrove</small>", unsafe_allow_html=True)
            
            if not df.empty:
                st.markdown(f"##### {t('results_data_structure')}")
                schema_df = pd.DataFrame({
                    t('results_column'): df.columns,
                    t('results_type'): [str(dtype) for dtype in df.dtypes]
                })
                st.dataframe(schema_df, use_container_width=True, hide_index=True)
        
        with tab_dashboard:
            if not df.empty:
                st.markdown(f"##### 📈 {t('dashboard_title')}")
                st.caption(t('dashboard_hint'))
                
                if st.button(f"🎯 {t('dashboard_generate')}", use_container_width=True, key="gen_dashboard"):
                    with st.spinner(t('dashboard_generating')):
                        data_list = df.to_dict(orient="records")
                        success, dashboard_data = generate_dashboard(data_list, "Dashboard DataPulse")
                    
                    if success:
                        st.success(f"✅ {t('dashboard_success')}")
                        
                        # Display widgets
                        if "widgets" in dashboard_data:
                            widgets = dashboard_data["widgets"]
                            
                            # Show widgets in grid
                            cols_per_row = 2
                            for i in range(0, len(widgets), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j in range(cols_per_row):
                                    if i + j < len(widgets):
                                        widget = widgets[i + j]
                                        with cols[j]:
                                            st.markdown(f"""
                                                <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                                                    <div style="font-size: 14px; color: #9ca3af; margin-bottom: 8px;">{widget.get('title', 'Widget')}</div>
                                                    <div style="font-size: 11px; color: #6b7280;">{t('chart_type')}: {widget.get('chart_type', 'auto')}</div>
                                                </div>
                                            """, unsafe_allow_html=True)
                                            
                                            # Create chart for widget
                                            widget_df = df.copy()
                                            chart_type = widget.get('chart_type', 'bar')
                                            if chart_type in ['bar', 'pie', 'line', 'scatter', 'metric']:
                                                create_chart(widget_df, chart_type)
                        
                        # Stats
                        if "stats" in dashboard_data:
                            st.markdown("---")
                            st.markdown(f"##### 📊 {t('dashboard_stats')}")
                            stats = dashboard_data.get("stats", {})
                            stat_cols = st.columns(3)
                            with stat_cols[0]:
                                st.metric(t('dashboard_rows'), stats.get("total_rows", len(df)))
                            with stat_cols[1]:
                                st.metric(t('dashboard_columns'), stats.get("total_columns", len(df.columns)))
                            with stat_cols[2]:
                                st.metric(t('dashboard_data_types'), len(df.dtypes.unique()))
                    else:
                        st.error(f"❌ {t('dashboard_error')}: {dashboard_data}")
            else:
                st.info(t('dashboard_run_query'))

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""
    <div style="text-align: center; padding: 24px; border-top: 1px solid #2a2a32; color: #6b7280; font-size: 13px;">
        {t('footer_text')}
    </div>
""", unsafe_allow_html=True)
