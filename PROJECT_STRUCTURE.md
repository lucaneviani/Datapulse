# DataPulse Repository Structure

This document provides an overview of the project structure for contributors and developers.

## 📁 Root Directory

```
Datapulse/
├── .github/              # GitHub configuration
│   ├── workflows/        # CI/CD workflows
│   └── ISSUE_TEMPLATE/   # Issue templates
├── backend/              # FastAPI backend application
├── frontend/             # Streamlit frontend application
├── data/                 # Database and sample data
├── tests/                # Test suite (pytest)
├── scripts/              # Utility scripts
├── exports/              # Export outputs directory
├── uploads/              # Upload storage directory
├── docs/                 # Documentation (if needed)
└── [config files]        # Various configuration files
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation and setup guide |
| `CONTRIBUTING.md` | Guidelines for contributing to the project |
| `CODE_OF_CONDUCT.md` | Community standards and behavior expectations |
| `SECURITY.md` | Security policy and vulnerability reporting |
| `SECURITY_AUDIT.md` | Comprehensive security assessment report |
| `CHANGELOG.md` | Version history and release notes |
| `LICENSE` | MIT License |
| `GITHUB_DEPLOYMENT.md` | GitHub deployment guide and checklist |

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `.env.example` | Environment variables template |
| `.gitignore` | Git ignore patterns |
| `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| `setup.cfg` | Tool configuration (flake8, isort, pytest) |
| `pyproject.toml` | Python project metadata and tool config |
| `docker-compose.yml` | Docker Compose configuration |
| `Dockerfile` | Docker image definition |

## 🐍 Backend Structure

```
backend/
├── main.py              # FastAPI application and endpoints
├── config.py            # Centralized configuration (Pydantic)
├── models.py            # Database models (SQLAlchemy)
├── schemas.py           # Request/response schemas (Pydantic)
├── auth.py              # JWT authentication system
├── ai_service.py        # Google Gemini AI integration
├── database_manager.py  # Session and database management
├── dashboard.py         # Dashboard generation
├── export_service.py    # Export functionality (PDF, Excel, etc.)
├── middleware.py        # Error handling middleware
├── logger.py            # Structured logging
├── i18n.py              # Internationalization (i18n)
└── requirements.txt     # Python dependencies
```

## 🎨 Frontend Structure

```
frontend/
├── app.py               # Streamlit application
└── requirements.txt     # Frontend dependencies (if separate)
```

## 🧪 Tests Structure

```
tests/
├── conftest.py                   # Pytest configuration and fixtures
├── test_api.py                   # API endpoint tests
├── test_auth.py                  # Authentication tests
├── test_ai_service.py            # AI service tests
├── test_database_manager.py      # Database manager tests
├── test_middleware.py            # Middleware tests
├── test_schemas.py               # Schema validation tests
└── test_ai_dynamic_fallback.py   # Fallback SQL generator tests
```

## 🗄️ Data Structure

```
data/
├── .gitkeep             # Keep directory in git
├── .jwt_secret          # JWT secret (auto-generated, gitignored)
├── users.db             # User database (gitignored)
├── database.db          # Demo database (gitignored)
├── populate_db.py       # Database population script
└── superstore_orders.csv # Sample dataset
```

## 📜 Scripts

```
scripts/
├── run_local.py         # Local development launcher
└── .gitkeep             # Keep directory in git
```

## 🐳 Docker

- **Dockerfile**: Multi-stage build for production
- **docker-compose.yml**: Complete stack (backend + frontend)

## 🚀 CI/CD Workflows

```
.github/workflows/
├── tests.yml            # Automated testing (Python 3.10, 3.11, 3.12)
└── lint.yml             # Code quality checks (flake8, black, isort)
```

## 📝 Key Files Description

### Backend Files

- **main.py** (976 lines): Core FastAPI application with all REST endpoints
- **ai_service.py** (749 lines): SQL generation with AI, caching, rate limiting
- **config.py**: Pydantic Settings for environment-based configuration
- **schemas.py**: Type-safe request/response models
- **auth.py**: JWT authentication with bcrypt password hashing
- **database_manager.py**: Session management for custom database uploads
- **middleware.py**: Centralized error handling with structured responses
- **logger.py**: JSON logging for production monitoring

### Frontend Files

- **app.py**: Streamlit web interface with interactive query UI

### Test Files

- **188+ tests** covering authentication, API endpoints, AI service, validation, and error handling
- **Fixtures**: Reusable test data and setup in `conftest.py`
- **Coverage**: All critical paths tested

## 🔒 Security

Key security features:
- SQL injection protection (multiple layers)
- JWT authentication
- Input sanitization
- Rate limiting
- CORS configuration
- File upload validation

See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for detailed security assessment.

## 🛠️ Development Workflow

1. **Clone repository**
2. **Create virtual environment**: `python -m venv venv`
3. **Install dependencies**: `pip install -r backend/requirements.txt`
4. **Configure environment**: `cp .env.example .env` and edit
5. **Run tests**: `python -m pytest`
6. **Start development**: `python scripts/run_local.py`

## 📦 Dependencies

### Core Dependencies
- **FastAPI 0.121+**: REST API framework
- **Streamlit 1.51+**: Web frontend
- **SQLAlchemy 2.0+**: Database ORM
- **Pydantic 2.0+**: Data validation
- **Google Generative AI**: Gemini integration (optional)

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **isort**: Import sorting
- **pre-commit**: Git hooks

## 🌐 Deployment

See [GITHUB_DEPLOYMENT.md](GITHUB_DEPLOYMENT.md) for complete deployment guide.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

**For detailed setup and usage instructions, see [README.md](README.md)**
