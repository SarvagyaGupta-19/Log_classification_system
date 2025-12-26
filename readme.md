# 🚀 Log Classification System

**Intelligent log classification using multi-stage ML pipeline: Regex → BERT → LLM**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.127.0-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 What This Does

Automatically classifies log messages into categories (User Actions, System Notifications, etc.) using:
- **Regex patterns** (fast, rule-based)
- **BERT embeddings** (ML-based, accurate)
- **LLM classification** (AI-powered for complex cases)

**Use Cases:** Security monitoring, log analytics, incident detection, compliance reporting

---

## ⚡ Quick Start

### 1. Setup
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure
Edit `.env` file:
```bash
GROQ_API_KEY=your_api_key_here  # Get from https://console.groq.com/keys
```

### 3. Run
```powershell
# Start server
uvicorn server:app --host 127.0.0.1 --port 8000

# Access API docs
# http://127.0.0.1:8000/docs
```

### 4. Test
```powershell
# Using PowerShell
$body = @{log_entries=@("User User123 logged in.")} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/classify/" -Method POST -ContentType "application/json" -Body $body

# Using curl
curl -X POST http://127.0.0.1:8000/classify/ -H "Content-Type: application/json" -d "{\"log_entries\":[\"User User123 logged in.\"]}"
```

---

## 🏗️ Architecture

```
┌─────────────┐
│  Log Input  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ LegacyCRM logs?  │
├──────────────────┤
│  YES → LLM       │─────────┐
│  NO  → Regex     │         │
└─────────┬────────┘         │
          │                  │
          ▼                  │
    ┌─────────┐              │
    │ Matched?│              │
    └────┬────┘              │
         │                   │
    NO   │   YES             │
         ▼    │              │
    ┌────────┐│              │
    │  BERT  ││              │
    └────────┘│              │
         │    │              │
         └────┴──────────────┘
              ▼
        Classification Result
```

---

## 📁 Project Structure

```
├── server.py              # FastAPI application
├── classify.py            # Classification orchestrator
├── processor_regex.py     # Pattern matching
├── processor_bert.py      # BERT embeddings
├── processor_llm.py       # LLM integration
├── config.py              # Configuration
├── models.py              # Pydantic models
├── exceptions.py          # Error handling
├── logger_config.py       # Structured logging
├── metrics.py             # Performance tracking
├── requirements.txt       # Dependencies
├── Dockerfile             # Container image
├── docker-compose.yml     # Service orchestration
└── models/
    └── log_classifier.joblib  # Trained model
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/metrics` | GET | Performance metrics |
| `/classify/` | POST | Classify log entries |
| `/classify/csv` | POST | Process CSV file |
| `/plot/` | POST | Generate analytics plot |
| `/docs` | GET | Interactive API docs |

---

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Server runs on: `http://localhost:8000`

---

## 📊 Current Capabilities

### ✅ **Working Features**
- Multi-stage classification (Regex → BERT → LLM)
- RESTful API with FastAPI
- Real-time health monitoring
- Performance metrics tracking
- Structured JSON logging
- CSV file processing
- Pydantic validation
- Error handling & retries
- Docker containerization
- Interactive API documentation

### 📝 **Classification Methods**
1. **Regex** (8 patterns): User login/logout, backups, system updates
2. **BERT** (ML model): Trained on 10,000+ log samples
3. **LLM** (Groq): llama-3.3-70b-versatile for complex patterns

### 📈 **Performance**
- Regex: <1ms per log
- BERT: ~50-100ms per log
- LLM: ~200-500ms per log
- Throughput: ~100-500 requests/minute

---

## 🚀 What's Needed to Finalize

### 🔴 **Critical (Must Fix)**

1. **Security Hardening**
   ```python
   # Add to server.py
   from fastapi import Security, HTTPException
   from fastapi.security.api_key import APIKeyHeader
   
   API_KEY = os.getenv("API_KEY")
   api_key_header = APIKeyHeader(name="X-API-Key")
   
   async def verify_api_key(api_key: str = Security(api_key_header)):
       if api_key != API_KEY:
           raise HTTPException(status_code=403, detail="Invalid API Key")
   ```

2. **Rate Limiting**
   ```bash
   pip install slowapi
   ```

3. **Database Integration**
   ```bash
   # Replace CSV with PostgreSQL
   pip install psycopg2-binary sqlalchemy
   ```

4. **Production Environment**
   - Set `debug=False` in config
   - Use proper secrets manager
   - Enable HTTPS/TLS
   - Configure proper CORS origins

### 🟡 **Important (Should Have)**

5. **Comprehensive Testing**
   ```bash
   pytest tests/ --cov=. --cov-report=html
   # Target: 80%+ coverage
   ```

6. **CI/CD Pipeline**
   ```yaml
   # .github/workflows/deploy.yml
   - Run tests
   - Build Docker image
   - Deploy to production
   ```

7. **Monitoring & Alerting**
   - Prometheus metrics export
   - Grafana dashboards
   - Error alerting (Sentry)

### 🟢 **Nice to Have (Enhancement)**

8. **Async Processing** - Celery/Redis for background jobs
9. **Caching Layer** - Redis for repeated classifications
10. **A/B Testing** - Compare model versions
11. **Auto-scaling** - Kubernetes deployment
12. **API Versioning** - `/v1/classify/` endpoints

---

## 📦 Dependencies

```
fastapi==0.127.0          # Web framework
uvicorn==0.40.0           # ASGI server
pydantic==2.12.5          # Validation
sentence-transformers     # BERT embeddings
scikit-learn==1.8.0       # ML model
groq==1.0.0               # LLM API
pandas==2.3.3             # Data processing
python-dotenv==1.2.1      # Environment vars
```

---

## 🛠️ Development

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov black flake8

# Run tests
pytest tests/ -v

# Format code
black .

# Lint
flake8 .

# Type check
mypy .
```

---

## 📊 Deployment Checklist

- [ ] Environment variables configured
- [ ] API key authentication enabled
- [ ] Rate limiting implemented
- [ ] Database connected (not CSV)
- [ ] HTTPS/TLS enabled
- [ ] Secrets in vault (not .env)
- [ ] CORS origins whitelisted
- [ ] Tests passing (80%+ coverage)
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Logging to external service
- [ ] Performance tested (load test)
- [ ] Documentation updated
- [ ] Docker image built & pushed
- [ ] Health checks configured

---

## 🎯 Immediate Next Steps

**To make this production-ready RIGHT NOW:**

1. **Add authentication** (30 min)
   - API key validation
   - Rate limiting

2. **Connect database** (1-2 hours)
   - PostgreSQL setup
   - Replace CSV operations

3. **Security audit** (1 hour)
   - Remove API key from .env
   - Use secrets manager
   - Configure proper CORS

4. **Write tests** (2-3 hours)
   - Unit tests: 100% coverage of classify.py
   - Integration tests: Full API flow
   - Load tests: 1000+ concurrent requests

5. **Deploy** (1 hour)
   - Push to Docker Hub
   - Deploy to cloud (AWS/Azure/GCP)
   - Configure CI/CD

**Total Time: 5-7 hours of focused work**

---

## 📧 Support

For issues and questions:
- Check `/docs` endpoint for API documentation
- Review logs: JSON formatted in console
- Health check: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

---

## 📜 License

MIT License - See LICENSE file for details

---

**Status:** ✅ Working locally | ⚠️ Needs security hardening for production
