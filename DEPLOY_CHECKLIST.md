# 🚀 DataPulse v2.1.0 - Production Deployment Checklist

## Overview

This checklist provides step-by-step instructions for deploying DataPulse to production. 
The application has been hardened with:

- ✅ Centralized configuration management (Pydantic Settings)
- ✅ Structured JSON logging for production
- ✅ Docker containerization with multi-stage builds
- ✅ Enhanced health checks
- ✅ Modern UI/UX with micro-animations
- ✅ 184 passing tests

---

## 📋 Pre-Deployment Checklist

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# ===== SECURITY (REQUIRED) =====
SECRET_KEY=your-super-secret-key-min-32-chars-here
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# ===== DATABASE =====
DATABASE_URL=sqlite:///./data/database/datapulse.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:5432/datapulse

# ===== AI SERVICE =====
GEMINI_API_KEY=your-google-gemini-api-key

# ===== APPLICATION =====
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# ===== RATE LIMITING =====
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_ENABLED=true

# ===== CACHE =====
CACHE_TTL_SECONDS=300
CACHE_ENABLED=true
```

### 2. Validate Configuration

```bash
# Check for configuration issues
python -c "from backend.config import get_settings; get_settings().validate_settings()"
```

---

## 🐳 Docker Deployment

### Option A: Docker Compose (Recommended)

```bash
# 1. Build and start all services
docker-compose up -d --build

# 2. Initialize the database (first time only)
docker-compose --profile init up db-init

# 3. Verify services are running
docker-compose ps

# 4. Check health
curl http://localhost:8000/health
curl http://localhost:8501/healthz
```

### Option B: Manual Docker Build

```bash
# Build the image
docker build -t datapulse:2.1.0 .

# Run the container
docker run -d \
  --name datapulse-backend \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env:ro \
  datapulse:2.1.0

# Run Streamlit frontend
docker run -d \
  --name datapulse-frontend \
  -p 8501:8501 \
  -e BACKEND_URL=http://datapulse-backend:8000 \
  datapulse:2.1.0 \
  streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0
```

---

## 🖥️ Manual Deployment (No Docker)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Initialize Database

```bash
python data/populate_db.py
```

### 3. Start Backend

```bash
# Production with Gunicorn (recommended for Linux)
gunicorn backend.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -

# Or with Uvicorn directly
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Start Frontend

```bash
streamlit run frontend/app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true
```

---

## 🔒 Security Hardening

### Required Steps

- [ ] **Change SECRET_KEY**: Generate a strong random key (min 32 chars)
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- [ ] **Configure ALLOWED_ORIGINS**: List only trusted domains

- [ ] **Enable HTTPS**: Use a reverse proxy (Nginx, Traefik, Caddy)

- [ ] **Set APP_ENV=production**: Disables debug features

### Nginx Reverse Proxy Example

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 📊 Monitoring & Observability

### Health Check Endpoints

| Endpoint | Description | Expected Response |
|----------|-------------|-------------------|
| `GET /health` | Full system health | `{"status": "healthy", "checks": {...}}` |
| `GET /api/health` | API health | `{"status": "healthy"}` |
| `GET /docs` | OpenAPI documentation | Swagger UI |

### Log Analysis

Production logs are JSON-formatted for easy parsing:

```bash
# View logs
docker-compose logs -f backend

# Parse with jq
docker-compose logs backend | jq 'select(.level == "ERROR")'
```

### Recommended Monitoring Stack

- **Prometheus + Grafana**: Metrics visualization
- **Loki**: Log aggregation
- **Sentry**: Error tracking

---

## 🧪 Post-Deployment Validation

### 1. Health Check

```bash
curl -s http://localhost:8000/health | jq
```

Expected output:
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "checks": {
    "database": "connected",
    "ai_service": "configured",
    "cache": "active"
  }
}
```

### 2. API Test

```bash
# Login (use credentials created during setup)
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```
```

### 3. Frontend Access

Open `http://localhost:8501` in a browser.

---

## 🔄 Rollback Procedure

If issues occur after deployment:

```bash
# 1. Stop current containers
docker-compose down

# 2. Restore previous image
docker tag datapulse:previous datapulse:2.1.0

# 3. Restart
docker-compose up -d
```

---

## 📁 File Structure After Deployment

```
datapulse/
├── .env                    # Environment variables (not in git)
├── docker-compose.yml      # Container orchestration
├── Dockerfile              # Container image definition
├── backend/
│   ├── config.py          # Centralized configuration
│   ├── logger.py          # Structured logging
│   ├── main.py            # FastAPI application
│   └── ...
├── frontend/
│   └── app.py             # Streamlit UI
├── data/
│   └── database/          # SQLite database files
│       └── datapulse.db
├── exports/               # Generated reports
└── uploads/               # User uploads
```

---

## ✅ Final Checklist

Before going live:

- [ ] `.env` file configured with production values
- [ ] `SECRET_KEY` changed from default
- [ ] `ALLOWED_ORIGINS` restricted to your domains
- [ ] Database initialized with `populate_db.py`
- [ ] Health endpoint responding correctly
- [ ] HTTPS configured via reverse proxy
- [ ] Log rotation configured
- [ ] Backup strategy in place for database
- [ ] Monitoring/alerting configured

---

## 📞 Support

- **Issues**: Open a GitHub issue
- **Documentation**: See `/docs` endpoint for API documentation
- **Version**: 2.1.0

---

*Last updated: 2025*
