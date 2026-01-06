# Production Deployment Guide

## 🔒 Security Checklist

### Before Production Deployment

- [ ] **Environment Configuration**
  - [ ] Set `ENVIRONMENT=production` in .env
  - [ ] Set `DEBUG=False` in .env
  - [ ] Set `LOG_LEVEL=INFO` or `WARNING` in .env
  - [ ] Configure valid `GROQ_API_KEY`
  - [ ] Verify .env is in .gitignore
  - [ ] Never commit .env or API keys to version control

- [ ] **CORS Configuration**
  - [ ] Update allowed origins in `server.py` (line 82-86)
  - [ ] Remove `localhost` and `127.0.0.1` from production
  - [ ] Add your production domain(s)
  ```python
  allow_origins=[
      "https://yourdomain.com",
      "https://www.yourdomain.com",
  ]
  ```

- [ ] **File Upload Security**
  - [ ] Verify `MAX_FILE_SIZE_MB=50` is appropriate
  - [ ] Consider rate limiting for production
  - [ ] Validate file extensions (already implemented)
  - [ ] Sanitize filenames (already implemented)

- [ ] **API Keys**
  - [ ] Store API keys in secure vault (AWS Secrets, Azure Key Vault)
  - [ ] Never log API keys
  - [ ] Rotate keys periodically
  - [ ] Monitor API usage

## 📦 Deployment Options

### Option 1: Local Server

**Quick deployment for internal use:**

```bash
# 1. Clone repository
git clone https://github.com/SarvagyaGupta-19/Log_classification_system.git
cd Log_classification_system

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your settings

# 5. Run server
python server.py
```

**Access:** http://localhost:8000

### Option 2: Docker Deployment

**Containerized deployment for scalability:**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "server.py"]
```

```bash
# Build image
docker build -t log-classifier:1.0 .

# Run container
docker run -d \
  --name log-classifier \
  -p 8000:8000 \
  -e GROQ_API_KEY=your_key_here \
  -e ENVIRONMENT=production \
  -e DEBUG=False \
  -v $(pwd)/models:/app/models \
  log-classifier:1.0
```

### Option 3: Cloud Deployment

#### AWS Elastic Beanstalk

```bash
# 1. Install EB CLI
pip install awsebcli

# 2. Initialize EB
eb init -p python-3.10 log-classifier --region us-east-1

# 3. Create environment
eb create log-classifier-prod

# 4. Set environment variables
eb setenv GROQ_API_KEY=your_key \
  ENVIRONMENT=production \
  DEBUG=False

# 5. Deploy
eb deploy
```

#### Azure App Service

```bash
# 1. Create resource group
az group create --name log-classifier --location eastus

# 2. Create app service plan
az appservice plan create --name log-plan \
  --resource-group log-classifier \
  --sku B1 --is-linux

# 3. Create web app
az webapp create --resource-group log-classifier \
  --plan log-plan \
  --name log-classifier \
  --runtime "PYTHON:3.10"

# 4. Configure settings
az webapp config appsettings set \
  --resource-group log-classifier \
  --name log-classifier \
  --settings GROQ_API_KEY=your_key \
    ENVIRONMENT=production \
    DEBUG=False

# 5. Deploy code
az webapp up --name log-classifier
```

## 🔧 Production Configuration

### Environment Variables

| Variable | Production Value | Description |
|----------|------------------|-------------|
| `ENVIRONMENT` | `production` | Enables production optimizations |
| `DEBUG` | `False` | **CRITICAL**: Disables debug mode |
| `LOG_LEVEL` | `INFO` or `WARNING` | Reduces log verbosity |
| `GROQ_API_KEY` | Your API key | Required for LLM classification |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload file size |

### Server Configuration

**For production workloads, use a production ASGI server:**

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

**Nginx reverse proxy (recommended):**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

## 🚀 Performance Optimization

### Model Loading

- BERT model loads on first classification (~3-5 seconds)
- Cached for subsequent requests
- Consider preloading in startup (uncomment in `server.py`)

### Scaling Strategies

1. **Vertical Scaling**: Increase CPU/RAM for single instance
   - Recommended: 2+ CPU cores, 4+ GB RAM
   
2. **Horizontal Scaling**: Run multiple instances behind load balancer
   - Use shared storage for models
   - Consider Redis for caching
   
3. **Async Processing**: For large batch uploads
   - Implement queue system (Celery + Redis)
   - Return job ID, poll for results

### Monitoring

**Health endpoint**: `GET /health`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "bert_loaded": true,
  "llm_configured": true
}
```

**Metrics endpoint**: `GET /metrics`
```json
{
  "uptime_seconds": 3600,
  "total_requests": 1234,
  "classifications": {
    "regex": 800,
    "bert": 400,
    "llm": 34
  }
}
```

## 🛡️ Backup and Recovery

### Model Backups

```bash
# Backup trained BERT model
cp models/log_classifier.joblib backups/log_classifier_$(date +%Y%m%d).joblib
```

### Database (if added)

```bash
# PostgreSQL backup
pg_dump log_classifier > backup_$(date +%Y%m%d).sql

# MongoDB backup
mongodump --db log_classifier --out backups/
```

## 📊 Monitoring and Logging

### Log Aggregation

**Structured JSON logs** are output to stdout. Configure log aggregation:

- **ELK Stack**: Elasticsearch + Logstash + Kibana
- **CloudWatch Logs**: AWS native logging
- **Application Insights**: Azure monitoring
- **Datadog/New Relic**: Third-party APM

### Alerts

Set up alerts for:
- High error rates (>5% of requests)
- API failures (LLM/BERT errors)
- High latency (>5 seconds per classification)
- Resource exhaustion (memory, disk)

## 🧪 Testing Before Production

### 1. Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test single endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test classification endpoint
ab -n 100 -c 5 -p test.csv \
  -T "multipart/form-data" \
  http://localhost:8000/api/classify-csv
```

### 2. Integration Testing

```bash
# Run test suite
python -m pytest tests/ -v

# Check API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### 3. Security Scanning

```bash
# Check for vulnerabilities
pip install safety
safety check -r requirements.txt

# Code security analysis
pip install bandit
bandit -r . -ll
```

## 📝 Post-Deployment Checklist

- [ ] Server is running and accessible
- [ ] Health endpoint returns `healthy`
- [ ] Dashboard loads correctly
- [ ] File upload works (test all formats)
- [ ] Classifications are accurate
- [ ] Results download as CSV
- [ ] Logs are being generated
- [ ] Metrics are tracking correctly
- [ ] Error handling works (test invalid inputs)
- [ ] API key is validated
- [ ] CORS is restricted to production domains
- [ ] SSL/TLS certificate is valid (HTTPS)
- [ ] Monitoring alerts are configured
- [ ] Backup strategy is in place

## 🔄 Updates and Maintenance

### Update Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all packages (carefully!)
pip install --upgrade -r requirements.txt
```

### Model Updates

When updating the BERT model:
1. Train new model with updated dataset
2. Save to `models/log_classifier_v2.joblib`
3. Test thoroughly in staging
4. Update `classifier_model_path` in config
5. Deploy with zero-downtime strategy

## 🆘 Troubleshooting

### Common Issues

**Issue**: "GROQ_API_KEY not set"
- **Solution**: Configure API key in .env file

**Issue**: BERT model loading is slow
- **Solution**: Preload model in startup or use model caching

**Issue**: Out of memory errors
- **Solution**: Increase RAM or reduce batch size

**Issue**: File upload fails
- **Solution**: Check MAX_FILE_SIZE_MB setting and nginx client_max_body_size

### Support

- GitHub Issues: https://github.com/SarvagyaGupta-19/Log_classification_system/issues
- Documentation: See README.md
- Email: your-email@example.com

## 📄 License

MIT License - See LICENSE file for details
