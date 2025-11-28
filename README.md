# 📊 DataPulse

<div align="center">

**AI-Powered Business Intelligence Tool**

*Interroga i tuoi dati aziendali usando il linguaggio naturale*

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🎯 Panoramica

**DataPulse** è un'applicazione di business intelligence che permette di interrogare database SQL usando domande in linguaggio naturale. Grazie all'integrazione con Google Gemini AI, converte automaticamente le tue domande in query SQL sicure e restituisce i risultati in forma tabellare o grafica.

### ✨ Funzionalità Principali

- 🤖 **Generazione SQL con AI** - Converti domande naturali in query SQL valide
- 🔒 **Sicurezza Integrata** - Validazione SQL, whitelist tabelle, protezione injection
- 📈 **Visualizzazioni Automatiche** - Grafici dinamici con Plotly (bar, pie, line)
- ⚡ **Caching Intelligente** - Cache query per prestazioni ottimali
- 🛡️ **Rate Limiting** - Protezione API key con limiti richieste
- 📊 **Dashboard Interattiva** - Interfaccia Streamlit moderna e responsive

---

## 🏗️ Architettura

```
DataPulse/
├── backend/                 # API FastAPI
│   ├── main.py             # Endpoint principali
│   ├── ai_service.py       # Integrazione Gemini AI
│   ├── models.py           # Modelli SQLAlchemy
│   └── requirements.txt    # Dipendenze Python
├── frontend/               # UI Streamlit
│   └── app.py              # Dashboard interattiva
├── data/                   # Database e dati
│   ├── database.db         # SQLite database
│   ├── populate_db.py      # Script popolamento
│   └── superstore_orders.csv
├── tests/                  # Unit tests
│   ├── test_ai_service.py  # Test AI e validazione
│   ├── test_api.py         # Test endpoint API
│   └── conftest.py         # Fixtures pytest
├── .env.example            # Template variabili ambiente
└── README.md               # Questa documentazione
```

---

## 🚀 Quick Start

### Prerequisiti

- **Python 3.12+** ([Download](https://python.org))
- **Git** ([Download](https://git-scm.com))
- **API Key Google Gemini** ([Ottieni qui](https://aistudio.google.com/app/apikey))

### 1. Clona il Repository

```bash
git clone https://github.com/lucaneviani/Datapulse.git
cd Datapulse
```

### 2. Crea Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Installa Dipendenze

```bash
pip install -r backend/requirements.txt
```

### 4. Configura API Key

```bash
# Copia il template
cp .env.example .env

# Modifica .env con la tua chiave API
# GOOGLE_API_KEY=your_gemini_api_key_here
```

> 💡 **Come ottenere la chiave API:**
> 1. Vai su [Google AI Studio](https://aistudio.google.com/app/apikey)
> 2. Crea un nuovo progetto o seleziona esistente
> 3. Genera una nuova API key
> 4. Copia la chiave nel file `.env`

### 5. Popola il Database (opzionale)

Se il database non esiste o vuoi ripopolarlo:

```bash
python data/populate_db.py
```

### 6. Avvia l'Applicazione

**Terminal 1 - Backend:**
```bash
python -m uvicorn backend.main:app --reload
```
> Server disponibile su: http://127.0.0.1:8000

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/app.py
```
> Dashboard disponibile su: http://localhost:8501

---

## 💻 Utilizzo

### Interfaccia Web (Streamlit)

1. Apri http://localhost:8501 nel browser
2. Inserisci una domanda nel campo di testo, es:
   - *"Quanti clienti ci sono?"*
   - *"Qual è il totale delle vendite per regione?"*
   - *"Mostra i top 5 prodotti per profitto"*
3. Clicca **Analizza**
4. Visualizza SQL generato e risultati (tabella o grafico)

### API REST (Swagger)

Accedi alla documentazione interattiva: http://127.0.0.1:8000/docs

**Esempio richiesta:**
```bash
curl -X POST "http://127.0.0.1:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers are there?"}'
```

**Esempio risposta:**
```json
{
  "generated_sql": "SELECT COUNT(*) as customer_count FROM customers;",
  "data": [{"customer_count": 793}],
  "row_count": 1
}
```

---

## 📊 Schema Database

Il database include 4 tabelle principali:

| Tabella | Descrizione | Colonne Principali |
|---------|-------------|-------------------|
| `customers` | Anagrafica clienti | id, name, segment, region, country |
| `products` | Catalogo prodotti | id, name, category, sub_category |
| `orders` | Ordini | id, customer_id, order_date, total |
| `order_items` | Dettaglio ordini | id, order_id, product_id, quantity, profit |

### Esempi di Domande

| Domanda | SQL Generato |
|---------|--------------|
| Quanti clienti ci sono? | `SELECT COUNT(*) FROM customers;` |
| Vendite per regione | `SELECT region, SUM(total) FROM orders JOIN customers...` |
| Top 5 prodotti | `SELECT name, SUM(profit) FROM products JOIN order_items... LIMIT 5` |
| Ordini 2023 | `SELECT * FROM orders WHERE strftime('%Y', order_date) = '2023'` |

---

## 🔒 Sicurezza

DataPulse implementa multiple protezioni:

- ✅ **Solo SELECT** - Query di modifica (INSERT, UPDATE, DELETE) bloccate
- ✅ **Whitelist Tabelle** - Solo tabelle autorizzate accessibili
- ✅ **Blocco UNION** - Previene lettura dati non autorizzati
- ✅ **Sanitizzazione Input** - Protezione XSS e injection
- ✅ **Rate Limiting** - 30 richieste/minuto per proteggere API
- ✅ **No SQL Comments** - Commenti SQL bloccati

---

## 🧪 Testing

Esegui tutti i test:

```bash
python -m pytest tests/ -v
```

Output atteso: **57 test passati**

### Coverage dei Test

- `test_ai_service.py` - Validazione SQL, cache, rate limiting, sanitizzazione
- `test_api.py` - Endpoint API, error handling, integrazione

---

## 📁 API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Genera SQL e restituisce dati |
| `GET` | `/health` | Health check del server |
| `GET` | `/api/cache/stats` | Statistiche cache |
| `POST` | `/api/cache/clear` | Svuota cache |
| `GET` | `/api/schema/tables` | Lista tabelle permesse |

---

## ⚙️ Configurazione

### Variabili Ambiente (.env)

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `GOOGLE_API_KEY` | API key Google Gemini | *obbligatorio* |
| `DATAPULSE_BACKEND_URL` | URL backend per frontend | `http://127.0.0.1:8000/api/analyze` |
| `DATAPULSE_MAX_ROWS` | Max righe restituite | `1000` |
| `DATAPULSE_CACHE_TTL` | TTL cache in secondi | `3600` |
| `DATAPULSE_RATE_LIMIT` | Richieste/minuto | `30` |

---

## 🛠️ Tecnologie

| Componente | Tecnologia |
|------------|------------|
| Backend | FastAPI, SQLAlchemy, Uvicorn |
| Frontend | Streamlit, Plotly, Pandas |
| AI | Google Gemini (gemini-2.0-flash-exp) |
| Database | SQLite |
| Testing | Pytest |

---

## 🤝 Contributing

1. Fork del repository
2. Crea un branch (`git checkout -b feature/nuova-feature`)
3. Commit delle modifiche (`git commit -m 'Aggiunta nuova feature'`)
4. Push al branch (`git push origin feature/nuova-feature`)
5. Apri una Pull Request

---

## 📝 License

Questo progetto è distribuito sotto licenza MIT. Vedi il file [LICENSE](LICENSE) per dettagli.

---

## 👨‍💻 Autore

**Luca Neviani** - [GitHub](https://github.com/lucaneviani)

---

<div align="center">

Made with ❤️ using visual studio code

</div>