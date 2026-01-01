# 🚀 DEPLOYMENT GUIDE

## Production Deployment Checklist

### **Phase 1: Prerequisites**

```bash
# System Requirements
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- 4GB RAM minimum
- 20GB disk space
```

### **Phase 2: Environment Configuration**

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Configure critical settings:**
```env
# Production Security
JWT_SECRET_KEY=<generate-strong-256-bit-key>
GROQ_API_KEY=<your-groq-api-key>

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/logclassifier

# Environment
ENVIRONMENT=production
DEBUG=false
```

3. **Generate secure JWT secret:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### **Phase 3: Docker Deployment (Recommended)**

```bash
# Build and start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f web
```

**Services Started:**
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ FastAPI Web (port 8000)
- ✅ Celery Worker
- ✅ Celery Beat

### **Phase 4: Manual Deployment**

1. **Install dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Initialize database:**
```bash
python database.py
```

3. **Start services:**

Terminal 1 - Web Server:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

Terminal 2 - Celery Worker:
```bash
celery -A tasks worker --loglevel=info
```

Terminal 3 - Celery Beat:
```bash
celery -A tasks beat --loglevel=info
```

### **Phase 5: Verification**

1. **Health Check:**
```bash
curl http://localhost:8000/health
```

2. **Login Test:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123"
```

3. **Access Dashboard:**
```
http://localhost:8000
```

**Default Credentials:**
- Admin: `admin` / `admin123`
- Analyst: `analyst` / `analyst123`
- Viewer: `demo` / `demo123`

### **Phase 6: Production Hardening**

1. **Change all default passwords**
2. **Enable HTTPS (reverse proxy with nginx)**
3. **Configure firewall rules**
4. **Set up log aggregation (ELK Stack)**
5. **Configure monitoring (Prometheus/Grafana)**
6. **Set up automated backups**

### **Phase 7: Scaling**

**Horizontal Scaling:**
```yaml
# docker-compose.yml
services:
  web:
    deploy:
      replicas: 4  # Multiple instances
  
  celery_worker:
    deploy:
      replicas: 8  # Scale workers
```

**Load Balancer (nginx):**
```nginx
upstream backend {
    server web:8000 weight=3;
    server web2:8000 weight=2;
}
```

### **Phase 8: Monitoring**

**Endpoints for Monitoring Tools:**
- Health: `GET /health`
- Metrics: `GET /metrics`
- OpenAPI: `GET /docs`

**Grafana Dashboard Queries:**
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_errors_total[5m])

# Processing time P95
histogram_quantile(0.95, rate(processing_time_bucket[5m]))
```

---

## **Troubleshooting**

### **Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose ps db

# View logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d
```

### **Celery Worker Not Processing**
```bash
# Check Redis connection
redis-cli ping

# Restart worker
docker-compose restart celery_worker
```

### **Model Loading Errors**
```bash
# Download BERT model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Check model file
ls -lh models/log_classifier.joblib
```

---

## **Backup & Recovery**

### **Database Backup**
```bash
# Backup
docker-compose exec db pg_dump -U loguser log_classifier > backup.sql

# Restore
docker-compose exec -T db psql -U loguser log_classifier < backup.sql
```

### **Application Backup**
```bash
tar -czf logclassifier-backup.tar.gz \
  .env models/ resources/ database/
```

---

## **Performance Tuning**

### **Database Optimization**
```sql
-- Create indexes
CREATE INDEX idx_job_status ON classification_jobs(status);
CREATE INDEX idx_result_label ON classification_results(target_label);
```

### **Worker Optimization**
```bash
# Increase workers
celery -A tasks worker --concurrency=16 --loglevel=info

# Enable prefork pool
celery -A tasks worker --pool=prefork
```

---

## **Security Checklist**

- [ ] Changed all default passwords
- [ ] JWT secret key is strong and unique
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Database credentials rotated
- [ ] API keys stored securely
- [ ] CORS configured properly
- [ ] Audit logging enabled
- [ ] Regular security updates
- [ ] Firewall rules configured

---

## **Support**

- **Documentation:** `/docs` endpoint
- **Issues:** GitHub Issues
- **Email:** sarvagya653@gmail.com
- **Repository:** https://github.com/SarvagyaGupta-19/Log_classification_system
