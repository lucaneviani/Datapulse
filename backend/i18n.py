"""
DataPulse Internationalization (i18n) System
=============================================

Sistema di traduzione multi-lingua per DataPulse.

Lingue supportate:
- Italiano (it) - Default
- English (en)
- Español (es)
- Français (fr)
- Deutsch (de)

Author: DataPulse Team
License: MIT
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger("datapulse.i18n")

# ============================================================================
# CONFIGURAZIONE LINGUE
# ============================================================================

SUPPORTED_LANGUAGES = {
    "it": {"name": "Italiano", "flag": "🇮🇹", "native": "Italiano"},
    "en": {"name": "English", "flag": "🇬🇧", "native": "English"},
    "es": {"name": "Spanish", "flag": "🇪🇸", "native": "Español"},
    "fr": {"name": "French", "flag": "🇫🇷", "native": "Français"},
    "de": {"name": "German", "flag": "🇩🇪", "native": "Deutsch"},
}

DEFAULT_LANGUAGE = "it"

# ============================================================================
# DIZIONARI TRADUZIONI
# ============================================================================

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ========================================================================
    # ITALIANO (Default)
    # ========================================================================
    "it": {
        # App General
        "app_name": "DataPulse",
        "app_tagline": "AI Analytics",
        "app_description": "Interroga i tuoi dati in linguaggio naturale. L'AI genera query SQL e visualizzazioni automatiche.",
        "app_description_custom": "Interroga il tuo database personalizzato in linguaggio naturale.",
        
        # Navigation
        "nav_home": "Home",
        "nav_dashboard": "Dashboard",
        "nav_settings": "Impostazioni",
        "nav_help": "Aiuto",
        
        # Authentication
        "auth_login": "Accedi",
        "auth_register": "Registrati",
        "auth_logout": "Logout",
        "auth_username": "Username",
        "auth_email": "Email",
        "auth_password": "Password",
        "auth_login_btn": "Accedi",
        "auth_register_btn": "Registrati",
        "auth_login_success": "Login effettuato con successo",
        "auth_register_success": "Registrazione completata",
        "auth_login_error": "Credenziali non valide",
        "auth_register_error": "Errore nella registrazione",
        "auth_password_hint": "Minimo 6 caratteri",
        "auth_fill_all": "Compila tutti i campi",
        "auth_password_short": "La password deve avere almeno 6 caratteri",
        "auth_logging_in": "Login in corso...",
        "auth_registering": "Registrazione in corso...",
        
        # Status
        "status_online": "Sistema Online",
        "status_offline": "Backend Offline",
        "status_custom_db": "Database Personalizzato",
        "status_demo_db": "Database Demo",
        
        # Upload
        "upload_title": "Carica i tuoi dati",
        "upload_csv_tab": "CSV/Excel",
        "upload_sqlite_tab": "SQLite",
        "upload_csv_hint": "Carica uno o più file CSV o Excel",
        "upload_sqlite_hint": "Carica un database SQLite esistente",
        "upload_select_files": "Seleziona file",
        "upload_files_selected": "file selezionati",
        "upload_btn_csv": "Carica CSV/Excel",
        "upload_btn_sqlite": "Carica SQLite",
        "upload_loading": "Caricamento in corso...",
        "upload_success": "File caricati con successo",
        "upload_error": "Errore durante il caricamento",
        "upload_reset": "Torna al database demo",
        "upload_resetting": "Reset in corso...",
        "upload_reset_success": "Database resettato",
        
        # Query
        "query_title": "Fai una domanda",
        "query_placeholder": "Es: Qual è il fatturato totale per regione?",
        "query_placeholder_custom": "Es: Quanti record ci sono nella tabella?",
        "query_btn": "Analizza",
        "query_empty": "Inserisci una domanda valida",
        "query_too_short": "La domanda è troppo corta",
        "query_analyzing": "Analisi in corso...",
        
        # Suggestions
        "suggestions_title": "Suggerimenti",
        "sug_total_sales": "Totale Vendite",
        "sug_by_region": "Per Regione",
        "sug_top_products": "Top Prodotti",
        "sug_orders": "Ordini",
        "sug_count_records": "Conta Record",
        "sug_show_data": "Mostra Dati",
        "sug_structure": "Struttura",
        "sug_statistics": "Statistiche",
        
        # Results
        "results_error": "Errore nell'analisi",
        "results_success": "Query completata",
        "results_rows": "righe",
        "results_columns": "colonne",
        "results_tab_chart": "Grafico",
        "results_tab_table": "Tabella",
        "results_tab_sql": "SQL",
        "results_tab_dashboard": "Dashboard",
        "results_no_data": "Nessun dato da visualizzare",
        "results_no_results": "La query non ha restituito risultati",
        "results_sql_generated": "SQL Generato",
        "results_data_structure": "Struttura Dati",
        "results_column": "Colonna",
        "results_type": "Tipo",
        
        # Charts
        "chart_type": "Tipo",
        "chart_auto": "Auto",
        "chart_bar": "Barre",
        "chart_pie": "Torta",
        "chart_line": "Linea",
        "chart_scatter": "Scatter",
        "chart_table": "Tabella",
        "chart_metric": "Metrica",
        
        # Dashboard
        "dashboard_title": "Dashboard Automatica",
        "dashboard_hint": "Genera una dashboard completa basata sui tuoi dati",
        "dashboard_generate": "Genera Dashboard",
        "dashboard_generating": "Generazione dashboard in corso...",
        "dashboard_success": "Dashboard generata!",
        "dashboard_error": "Errore nella generazione",
        "dashboard_stats": "Statistiche",
        "dashboard_rows": "Righe",
        "dashboard_columns": "Colonne",
        "dashboard_data_types": "Tipi Dati",
        "dashboard_run_query": "Esegui una query per generare una dashboard",
        
        # Export
        "export_title": "Esporta",
        "export_format": "Formato",
        "export_btn": "Esporta",
        "export_download": "Scarica",
        "export_generating": "Generazione",
        "export_error": "Errore durante l'export",
        "export_run_query": "Esegui una query per abilitare l'export",
        
        # History
        "history_title": "Cronologia",
        "history_empty": "Nessuna query eseguita",
        "history_clear": "Pulisci cronologia",
        
        # Schema
        "schema_title": "Schema Database",
        "schema_custom": "Database Personalizzato",
        "schema_tables": "Tabelle disponibili",
        
        # Settings
        "settings_language": "Lingua",
        "settings_theme": "Tema",
        "settings_theme_dark": "Scuro",
        "settings_theme_light": "Chiaro",
        
        # Footer
        "footer_text": "DataPulse AI Analytics",
        
        # Errors
        "error_connection": "Impossibile connettersi al backend",
        "error_timeout": "Timeout: il server non risponde",
        "error_generic": "Errore",
        "error_session_create": "Impossibile creare la sessione",
    },
    
    # ========================================================================
    # ENGLISH
    # ========================================================================
    "en": {
        # App General
        "app_name": "DataPulse",
        "app_tagline": "AI Analytics",
        "app_description": "Query your data in natural language. AI generates SQL queries and automatic visualizations.",
        "app_description_custom": "Query your custom database in natural language.",
        
        # Navigation
        "nav_home": "Home",
        "nav_dashboard": "Dashboard",
        "nav_settings": "Settings",
        "nav_help": "Help",
        
        # Authentication
        "auth_login": "Login",
        "auth_register": "Register",
        "auth_logout": "Logout",
        "auth_username": "Username",
        "auth_email": "Email",
        "auth_password": "Password",
        "auth_login_btn": "Sign In",
        "auth_register_btn": "Sign Up",
        "auth_login_success": "Login successful",
        "auth_register_success": "Registration completed",
        "auth_login_error": "Invalid credentials",
        "auth_register_error": "Registration error",
        "auth_password_hint": "Minimum 6 characters",
        "auth_fill_all": "Fill in all fields",
        "auth_password_short": "Password must be at least 6 characters",
        "auth_logging_in": "Logging in...",
        "auth_registering": "Registering...",
        
        # Status
        "status_online": "System Online",
        "status_offline": "Backend Offline",
        "status_custom_db": "Custom Database",
        "status_demo_db": "Demo Database",
        
        # Upload
        "upload_title": "Upload your data",
        "upload_csv_tab": "CSV/Excel",
        "upload_sqlite_tab": "SQLite",
        "upload_csv_hint": "Upload one or more CSV or Excel files",
        "upload_sqlite_hint": "Upload an existing SQLite database",
        "upload_select_files": "Select files",
        "upload_files_selected": "files selected",
        "upload_btn_csv": "Upload CSV/Excel",
        "upload_btn_sqlite": "Upload SQLite",
        "upload_loading": "Uploading...",
        "upload_success": "Files uploaded successfully",
        "upload_error": "Upload error",
        "upload_reset": "Return to demo database",
        "upload_resetting": "Resetting...",
        "upload_reset_success": "Database reset",
        
        # Query
        "query_title": "Ask a question",
        "query_placeholder": "E.g.: What is the total revenue by region?",
        "query_placeholder_custom": "E.g.: How many records are in the table?",
        "query_btn": "Analyze",
        "query_empty": "Enter a valid question",
        "query_too_short": "Question is too short",
        "query_analyzing": "Analyzing...",
        
        # Suggestions
        "suggestions_title": "Suggestions",
        "sug_total_sales": "Total Sales",
        "sug_by_region": "By Region",
        "sug_top_products": "Top Products",
        "sug_orders": "Orders",
        "sug_count_records": "Count Records",
        "sug_show_data": "Show Data",
        "sug_structure": "Structure",
        "sug_statistics": "Statistics",
        
        # Results
        "results_error": "Analysis error",
        "results_success": "Query completed",
        "results_rows": "rows",
        "results_columns": "columns",
        "results_tab_chart": "Chart",
        "results_tab_table": "Table",
        "results_tab_sql": "SQL",
        "results_tab_dashboard": "Dashboard",
        "results_no_data": "No data to display",
        "results_no_results": "Query returned no results",
        "results_sql_generated": "Generated SQL",
        "results_data_structure": "Data Structure",
        "results_column": "Column",
        "results_type": "Type",
        
        # Charts
        "chart_type": "Type",
        "chart_auto": "Auto",
        "chart_bar": "Bar",
        "chart_pie": "Pie",
        "chart_line": "Line",
        "chart_scatter": "Scatter",
        "chart_table": "Table",
        "chart_metric": "Metric",
        
        # Dashboard
        "dashboard_title": "Automatic Dashboard",
        "dashboard_hint": "Generate a complete dashboard based on your data",
        "dashboard_generate": "Generate Dashboard",
        "dashboard_generating": "Generating dashboard...",
        "dashboard_success": "Dashboard generated!",
        "dashboard_error": "Generation error",
        "dashboard_stats": "Statistics",
        "dashboard_rows": "Rows",
        "dashboard_columns": "Columns",
        "dashboard_data_types": "Data Types",
        "dashboard_run_query": "Run a query to generate a dashboard",
        
        # Export
        "export_title": "Export",
        "export_format": "Format",
        "export_btn": "Export",
        "export_download": "Download",
        "export_generating": "Generating",
        "export_error": "Export error",
        "export_run_query": "Run a query to enable export",
        
        # History
        "history_title": "History",
        "history_empty": "No queries executed",
        "history_clear": "Clear history",
        
        # Schema
        "schema_title": "Database Schema",
        "schema_custom": "Custom Database",
        "schema_tables": "Available tables",
        
        # Settings
        "settings_language": "Language",
        "settings_theme": "Theme",
        "settings_theme_dark": "Dark",
        "settings_theme_light": "Light",
        
        # Footer
        "footer_text": "DataPulse AI Analytics",
        
        # Errors
        "error_connection": "Cannot connect to backend",
        "error_timeout": "Timeout: server not responding",
        "error_generic": "Error",
        "error_session_create": "Cannot create session",
    },
    
    # ========================================================================
    # ESPAÑOL
    # ========================================================================
    "es": {
        # App General
        "app_name": "DataPulse",
        "app_tagline": "AI Analytics",
        "app_description": "Consulta tus datos en lenguaje natural. La IA genera consultas SQL y visualizaciones automáticas.",
        "app_description_custom": "Consulta tu base de datos personalizada en lenguaje natural.",
        
        # Navigation
        "nav_home": "Inicio",
        "nav_dashboard": "Dashboard",
        "nav_settings": "Configuración",
        "nav_help": "Ayuda",
        
        # Authentication
        "auth_login": "Iniciar sesión",
        "auth_register": "Registrarse",
        "auth_logout": "Cerrar sesión",
        "auth_username": "Usuario",
        "auth_email": "Correo",
        "auth_password": "Contraseña",
        "auth_login_btn": "Entrar",
        "auth_register_btn": "Registrarse",
        "auth_login_success": "Inicio de sesión exitoso",
        "auth_register_success": "Registro completado",
        "auth_login_error": "Credenciales inválidas",
        "auth_register_error": "Error de registro",
        "auth_password_hint": "Mínimo 6 caracteres",
        "auth_fill_all": "Complete todos los campos",
        "auth_password_short": "La contraseña debe tener al menos 6 caracteres",
        "auth_logging_in": "Iniciando sesión...",
        "auth_registering": "Registrando...",
        
        # Status
        "status_online": "Sistema en línea",
        "status_offline": "Backend desconectado",
        "status_custom_db": "Base de datos personalizada",
        "status_demo_db": "Base de datos demo",
        
        # Upload
        "upload_title": "Sube tus datos",
        "upload_csv_tab": "CSV/Excel",
        "upload_sqlite_tab": "SQLite",
        "upload_csv_hint": "Sube uno o más archivos CSV o Excel",
        "upload_sqlite_hint": "Sube una base de datos SQLite existente",
        "upload_select_files": "Seleccionar archivos",
        "upload_files_selected": "archivos seleccionados",
        "upload_btn_csv": "Subir CSV/Excel",
        "upload_btn_sqlite": "Subir SQLite",
        "upload_loading": "Subiendo...",
        "upload_success": "Archivos subidos correctamente",
        "upload_error": "Error al subir",
        "upload_reset": "Volver a la base de datos demo",
        "upload_resetting": "Restableciendo...",
        "upload_reset_success": "Base de datos restablecida",
        
        # Query
        "query_title": "Haz una pregunta",
        "query_placeholder": "Ej: ¿Cuál es el ingreso total por región?",
        "query_placeholder_custom": "Ej: ¿Cuántos registros hay en la tabla?",
        "query_btn": "Analizar",
        "query_empty": "Ingresa una pregunta válida",
        "query_too_short": "La pregunta es muy corta",
        "query_analyzing": "Analizando...",
        
        # Suggestions
        "suggestions_title": "Sugerencias",
        "sug_total_sales": "Ventas Totales",
        "sug_by_region": "Por Región",
        "sug_top_products": "Top Productos",
        "sug_orders": "Pedidos",
        "sug_count_records": "Contar Registros",
        "sug_show_data": "Mostrar Datos",
        "sug_structure": "Estructura",
        "sug_statistics": "Estadísticas",
        
        # Results
        "results_error": "Error en el análisis",
        "results_success": "Consulta completada",
        "results_rows": "filas",
        "results_columns": "columnas",
        "results_tab_chart": "Gráfico",
        "results_tab_table": "Tabla",
        "results_tab_sql": "SQL",
        "results_tab_dashboard": "Dashboard",
        "results_no_data": "Sin datos para mostrar",
        "results_no_results": "La consulta no devolvió resultados",
        "results_sql_generated": "SQL Generado",
        "results_data_structure": "Estructura de Datos",
        "results_column": "Columna",
        "results_type": "Tipo",
        
        # Charts
        "chart_type": "Tipo",
        "chart_auto": "Auto",
        "chart_bar": "Barras",
        "chart_pie": "Pastel",
        "chart_line": "Línea",
        "chart_scatter": "Dispersión",
        "chart_table": "Tabla",
        "chart_metric": "Métrica",
        
        # Dashboard
        "dashboard_title": "Dashboard Automático",
        "dashboard_hint": "Genera un dashboard completo basado en tus datos",
        "dashboard_generate": "Generar Dashboard",
        "dashboard_generating": "Generando dashboard...",
        "dashboard_success": "¡Dashboard generado!",
        "dashboard_error": "Error de generación",
        "dashboard_stats": "Estadísticas",
        "dashboard_rows": "Filas",
        "dashboard_columns": "Columnas",
        "dashboard_data_types": "Tipos de Datos",
        "dashboard_run_query": "Ejecuta una consulta para generar un dashboard",
        
        # Export
        "export_title": "Exportar",
        "export_format": "Formato",
        "export_btn": "Exportar",
        "export_download": "Descargar",
        "export_generating": "Generando",
        "export_error": "Error de exportación",
        "export_run_query": "Ejecuta una consulta para habilitar la exportación",
        
        # History
        "history_title": "Historial",
        "history_empty": "Sin consultas ejecutadas",
        "history_clear": "Limpiar historial",
        
        # Schema
        "schema_title": "Esquema de Base de Datos",
        "schema_custom": "Base de Datos Personalizada",
        "schema_tables": "Tablas disponibles",
        
        # Settings
        "settings_language": "Idioma",
        "settings_theme": "Tema",
        "settings_theme_dark": "Oscuro",
        "settings_theme_light": "Claro",
        
        # Footer
        "footer_text": "DataPulse AI Analytics",
        
        # Errors
        "error_connection": "No se puede conectar al backend",
        "error_timeout": "Tiempo agotado: el servidor no responde",
        "error_generic": "Error",
        "error_session_create": "No se puede crear la sesión",
    },
    
    # ========================================================================
    # FRANÇAIS
    # ========================================================================
    "fr": {
        # App General
        "app_name": "DataPulse",
        "app_tagline": "AI Analytics",
        "app_description": "Interrogez vos données en langage naturel. L'IA génère des requêtes SQL et des visualisations automatiques.",
        "app_description_custom": "Interrogez votre base de données personnalisée en langage naturel.",
        
        # Authentication
        "auth_login": "Connexion",
        "auth_register": "S'inscrire",
        "auth_logout": "Déconnexion",
        "auth_username": "Nom d'utilisateur",
        "auth_email": "E-mail",
        "auth_password": "Mot de passe",
        "auth_login_btn": "Se connecter",
        "auth_register_btn": "S'inscrire",
        "auth_login_success": "Connexion réussie",
        "auth_register_success": "Inscription terminée",
        "auth_login_error": "Identifiants invalides",
        "auth_register_error": "Erreur d'inscription",
        "auth_password_hint": "Minimum 6 caractères",
        "auth_fill_all": "Remplissez tous les champs",
        "auth_password_short": "Le mot de passe doit contenir au moins 6 caractères",
        "auth_logging_in": "Connexion en cours...",
        "auth_registering": "Inscription en cours...",
        
        # Status
        "status_online": "Système en ligne",
        "status_offline": "Backend hors ligne",
        "status_custom_db": "Base de données personnalisée",
        "status_demo_db": "Base de données démo",
        
        # Upload
        "upload_title": "Téléchargez vos données",
        "upload_csv_tab": "CSV/Excel",
        "upload_sqlite_tab": "SQLite",
        "upload_csv_hint": "Téléchargez un ou plusieurs fichiers CSV ou Excel",
        "upload_sqlite_hint": "Téléchargez une base SQLite existante",
        "upload_btn_csv": "Télécharger CSV/Excel",
        "upload_btn_sqlite": "Télécharger SQLite",
        "upload_loading": "Téléchargement...",
        "upload_success": "Fichiers téléchargés avec succès",
        "upload_error": "Erreur de téléchargement",
        "upload_reset": "Revenir à la base de données démo",
        
        # Query
        "query_title": "Posez une question",
        "query_placeholder": "Ex: Quel est le chiffre d'affaires total par région?",
        "query_placeholder_custom": "Ex: Combien d'enregistrements dans la table?",
        "query_btn": "Analyser",
        "query_empty": "Entrez une question valide",
        "query_too_short": "La question est trop courte",
        "query_analyzing": "Analyse en cours...",
        
        # Results
        "results_error": "Erreur d'analyse",
        "results_success": "Requête terminée",
        "results_rows": "lignes",
        "results_columns": "colonnes",
        "results_tab_chart": "Graphique",
        "results_tab_table": "Tableau",
        "results_tab_sql": "SQL",
        "results_tab_dashboard": "Tableau de bord",
        
        # Export
        "export_title": "Exporter",
        "export_btn": "Exporter",
        "export_download": "Télécharger",
        
        # History
        "history_title": "Historique",
        "history_empty": "Aucune requête exécutée",
        "history_clear": "Effacer l'historique",
        
        # Footer
        "footer_text": "DataPulse AI Analytics",
    },
    
    # ========================================================================
    # DEUTSCH
    # ========================================================================
    "de": {
        # App General
        "app_name": "DataPulse",
        "app_tagline": "AI Analytics",
        "app_description": "Fragen Sie Ihre Daten in natürlicher Sprache ab. KI generiert SQL-Abfragen und automatische Visualisierungen.",
        "app_description_custom": "Fragen Sie Ihre benutzerdefinierte Datenbank in natürlicher Sprache ab.",
        
        # Authentication
        "auth_login": "Anmelden",
        "auth_register": "Registrieren",
        "auth_logout": "Abmelden",
        "auth_username": "Benutzername",
        "auth_email": "E-Mail",
        "auth_password": "Passwort",
        "auth_login_btn": "Anmelden",
        "auth_register_btn": "Registrieren",
        "auth_login_success": "Erfolgreich angemeldet",
        "auth_register_success": "Registrierung abgeschlossen",
        "auth_login_error": "Ungültige Anmeldedaten",
        "auth_register_error": "Registrierungsfehler",
        "auth_password_hint": "Mindestens 6 Zeichen",
        
        # Status
        "status_online": "System online",
        "status_offline": "Backend offline",
        "status_custom_db": "Benutzerdefinierte Datenbank",
        "status_demo_db": "Demo-Datenbank",
        
        # Upload
        "upload_title": "Laden Sie Ihre Daten hoch",
        "upload_csv_tab": "CSV/Excel",
        "upload_sqlite_tab": "SQLite",
        "upload_btn_csv": "CSV/Excel hochladen",
        "upload_btn_sqlite": "SQLite hochladen",
        "upload_loading": "Wird hochgeladen...",
        "upload_success": "Dateien erfolgreich hochgeladen",
        "upload_error": "Upload-Fehler",
        
        # Query
        "query_title": "Stellen Sie eine Frage",
        "query_placeholder": "Z.B.: Wie hoch ist der Gesamtumsatz nach Region?",
        "query_btn": "Analysieren",
        "query_analyzing": "Analysiere...",
        
        # Results
        "results_error": "Analysefehler",
        "results_success": "Abfrage abgeschlossen",
        "results_rows": "Zeilen",
        "results_columns": "Spalten",
        "results_tab_chart": "Diagramm",
        "results_tab_table": "Tabelle",
        "results_tab_sql": "SQL",
        
        # Export
        "export_title": "Exportieren",
        "export_btn": "Exportieren",
        "export_download": "Herunterladen",
        
        # History
        "history_title": "Verlauf",
        "history_empty": "Keine Abfragen ausgeführt",
        "history_clear": "Verlauf löschen",
        
        # Footer
        "footer_text": "DataPulse AI Analytics",
    },
}


# ============================================================================
# CLASSE I18N MANAGER
# ============================================================================

class I18nManager:
    """
    Manager per il sistema di internazionalizzazione.
    """
    
    def __init__(self, default_lang: str = DEFAULT_LANGUAGE):
        """Inizializza con lingua di default."""
        self.current_lang = default_lang
        self._fallback_lang = "en"
    
    def set_language(self, lang_code: str) -> bool:
        """
        Imposta la lingua corrente.
        
        Args:
            lang_code: Codice lingua (es. 'it', 'en', 'es')
        
        Returns:
            True se la lingua è supportata
        """
        if lang_code in SUPPORTED_LANGUAGES:
            self.current_lang = lang_code
            logger.info(f"Lingua impostata: {lang_code}")
            return True
        logger.warning(f"Lingua non supportata: {lang_code}")
        return False
    
    def get_language(self) -> str:
        """Restituisce il codice lingua corrente."""
        return self.current_lang
    
    def get_languages(self) -> Dict:
        """Restituisce le lingue supportate."""
        return SUPPORTED_LANGUAGES
    
    def t(self, key: str, **kwargs) -> str:
        """
        Traduce una chiave nella lingua corrente.
        
        Args:
            key: Chiave di traduzione
            **kwargs: Variabili per interpolazione
        
        Returns:
            Stringa tradotta
        """
        # Cerca nella lingua corrente
        translation = TRANSLATIONS.get(self.current_lang, {}).get(key)
        
        # Fallback a inglese
        if translation is None:
            translation = TRANSLATIONS.get(self._fallback_lang, {}).get(key)
        
        # Fallback a italiano
        if translation is None:
            translation = TRANSLATIONS.get("it", {}).get(key)
        
        # Se non trovato, restituisci la chiave
        if translation is None:
            logger.warning(f"Traduzione mancante: {key} [{self.current_lang}]")
            return key
        
        # Interpolazione variabili
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Variabile mancante in traduzione: {e}")
        
        return translation
    
    def get_all_translations(self, lang: str = None) -> Dict[str, str]:
        """Restituisce tutte le traduzioni per una lingua."""
        if lang is None:
            lang = self.current_lang
        return TRANSLATIONS.get(lang, TRANSLATIONS.get(self._fallback_lang, {}))


# Istanza singleton
i18n = I18nManager()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def t(key: str, **kwargs) -> str:
    """Shortcut per traduzione."""
    return i18n.t(key, **kwargs)


def set_language(lang_code: str) -> bool:
    """Shortcut per impostare lingua."""
    return i18n.set_language(lang_code)


def get_language() -> str:
    """Shortcut per ottenere lingua corrente."""
    return i18n.get_language()


def get_supported_languages() -> Dict:
    """Restituisce le lingue supportate."""
    return SUPPORTED_LANGUAGES
