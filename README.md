# DataPulse

<div align="center">

**AI-Powered Business Intelligence Platform**

*Query your data using natural language*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/YOUR_USERNAME/Datapulse/workflows/Tests/badge.svg)](https://github.com/YOUR_USERNAME/Datapulse/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## Overview

**DataPulse** is a modern business intelligence platform that enables users to query SQL databases using natural language. Powered by Google Gemini AI, it automatically converts questions into secure SQL queries and presents results in interactive tables and charts.

Perfect for business analysts, data scientists, and anyone who needs quick insights from their data without writing SQL.

### ✨ Key Features

- 🤖 **AI-Powered SQL Generation** - Convert natural language to valid SQL queries
- 🔒 **Built-in Security** - SQL validation, table whitelist, injection protection
- 📊 **Automatic Visualizations** - Dynamic charts with Plotly (bar, pie, line)
- ⚡ **Smart Caching** - Query caching for optimal performance
- 🛡️ **Rate Limiting** - API protection with request limits
- 🎨 **Interactive Dashboard** - Modern, responsive Streamlit interface
- 🌍 **Multi-language Support** - Available in IT, EN, ES, FR, DE
- 📁 **Custom Database Upload** - Support for CSV, Excel, and SQLite files
- 🔐 **JWT Authentication** - Secure user management
- 🐳 **Docker Support** - Easy deployment with containers

---

## 📂 Project Structure

For detailed information, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

```
DataPulse/
├── backend/                 # FastAPI REST API
│   ├── main.py             # API endpoints
│   ├── config.py           # Configuration management
│   ├── ai_service.py       # AI integration
│   ├── auth.py             # JWT authentication
│   └── ...
├── frontend/               # Streamlit UI
├── tests/                  # Test suite (188+ tests)
├── .github/                # CI/CD workflows
├── scripts/                # Utility scripts
└── docs/                   # Documentation
```

---

## Quick Start

### Prerequisites

- **Python 3.12+** ([Download](https://python.org))
- **Git** ([Download](https://git-scm.com))
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))

### 1. Clone the Repository

```bash
git clone https://github.com/lucaneviani/Datapulse.git
cd Datapulse
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure API Key

```bash
# Copy the template
cp .env.example .env

# Edit .env with your API key
# GOOGLE_API_KEY=your_gemini_api_key_here
```

> **How to get an API key:**
> 1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
> 2. Create a new project or select existing
> 3. Generate a new API key
> 4. Paste the key in your `.env` file

### 5. Populate Database (optional)

If the database doesn't exist or you want to repopulate it:

```bash
python data/populate_db.py
```

### 6. Start the Application

The repository includes a small launcher that starts both backend and frontend with sensible defaults and environment handling.

Recommended (single command):

- Windows (PowerShell):
```powershell
# From project root
.\start.ps1
```

- macOS / Linux:
```bash
# From project root
./start.sh
```

Or use the Python launcher (cross-platform):
```bash
# From project root
python scripts/run_local.py
```

The launcher will:
- load `.env` (if present)
- select default ports (`8000` backend, `8501` frontend) or pick free ports if those are in use
- start the backend (uvicorn) and wait for the health endpoint
- start the frontend (Streamlit) and open the UI in your browser

If you prefer manual start, you can still run:

**Backend (manual):**
```bash
python -m uvicorn backend.main:app --reload
```

**Frontend (manual):**
```bash
streamlit run frontend/app.py
```

> API available at: http://127.0.0.1:8000 (unless launcher selected another free port)

---

## Usage

### Web Interface (Streamlit)

1. Open http://localhost:8501 in your browser
2. Enter a question in the text field, e.g.:
   - *"How many customers are there?"*
   - *"What are the total sales by region?"*
   - *"Show top 5 products by profit"*
3. Click **Analyze**
4. View generated SQL and results (table or chart)

### REST API (Swagger)

Access interactive documentation at: http://127.0.0.1:8000/docs

**Example request:**
```bash
curl -X POST "http://127.0.0.1:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers are there?"}'
```

**Example response:**
```json
{
  "generated_sql": "SELECT COUNT(*) as customer_count FROM customers;",
  "data": [{"customer_count": 793}],
  "row_count": 1
}
```

---

## Database Schema

The database includes 4 main tables:

| Table | Description | Main Columns |
|-------|-------------|---------------|
| `customers` | Customer records | id, name, segment, region, country |
| `products` | Product catalog | id, name, category, sub_category |
| `orders` | Orders | id, customer_id, order_date, total |
| `order_items` | Order details | id, order_id, product_id, quantity, profit |

### Example Questions

| Question | Generated SQL |
|----------|---------------|
| How many customers? | `SELECT COUNT(*) FROM customers;` |
| Sales by region | `SELECT region, SUM(total) FROM orders JOIN customers...` |
| Top 5 products | `SELECT name, SUM(profit) FROM products JOIN order_items... LIMIT 5` |
| 2023 orders | `SELECT * FROM orders WHERE strftime('%Y', order_date) = '2023'` |

---

## Security

DataPulse implements multiple protection layers:

- **SELECT Only** - Modification queries (INSERT, UPDATE, DELETE) are blocked
- **Table Whitelist** - Only authorized tables are accessible
- **UNION Blocking** - Prevents unauthorized data access
- **Input Sanitization** - XSS and injection protection
- **Rate Limiting** - 30 requests/minute to protect the API
- **No SQL Comments** - SQL comments are blocked

---

## Testing

Run all tests:

```bash
python -m pytest tests/ -v
```

### Test Coverage

- `test_ai_service.py` - SQL validation, cache, rate limiting, sanitization
- `test_api.py` - API endpoints, error handling, integration

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Generate SQL and return data |
| `GET` | `/health` | Server health check |
| `GET` | `/api/cache/stats` | Cache statistics |
| `POST` | `/api/cache/clear` | Clear cache |
| `GET` | `/api/schema/tables` | List allowed tables |
| `POST` | `/api/auth/login` | User login |
| `POST` | `/api/auth/register` | User registration |
| `POST` | `/api/export` | Export data |

---

## Configuration

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|--------|
| `GOOGLE_API_KEY` | Google Gemini API key | *required* |
| `JWT_SECRET_KEY` | JWT signing key | *auto-generated* |
| `DATAPULSE_MAX_ROWS` | Max rows returned | `1000` |
| `DATAPULSE_CACHE_TTL` | Cache TTL in seconds | `3600` |
| `DATAPULSE_RATE_LIMIT` | Requests per minute | `30` |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, SQLAlchemy, Uvicorn |
| Frontend | Streamlit, Plotly, Pandas |
| AI | Google Gemini (gemini-2.0-flash-exp) |
| Database | SQLite |
| Auth | JWT, bcrypt |
| Testing | Pytest |

---

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

Quick start:
1. Fork the repository
2. Create a branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) and [Security Policy](SECURITY.md).

---

## Support

- 📖 [Documentation](README.md)
- 🐛 [Report a Bug](https://github.com/YOUR_USERNAME/Datapulse/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/YOUR_USERNAME/Datapulse/issues/new?template=feature_request.md)
- 💬 [Discussions](https://github.com/YOUR_USERNAME/Datapulse/discussions)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Author

**Luca Neviani** - [GitHub](https://github.com/lucaneviani)

---

<div align="center">

Built with ❤️ using FastAPI, Streamlit, and Google Gemini AI

</div>