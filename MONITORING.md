# Monitoring & Logging Integration Guide

## Overview

The Log Classification System uses **structured JSON logging** for production monitoring. This guide shows how to integrate with popular log aggregation and monitoring platforms.

## Built-in Logging

### Log Format

All logs are output to stdout in structured JSON format:

```json
{
  "timestamp": "2026-01-06T10:30:45.123Z",
  "level": "INFO",
  "logger": "server",
  "message": "Request completed",
  "request_id": "abc123-def456",
  "method": "POST",
  "path": "/api/classify-csv",
  "status_code": 200,
  "duration_ms": 245.67
}
```

### Log Levels

Configure via `LOG_LEVEL` environment variable:
- **DEBUG**: Development/troubleshooting
- **INFO**: Normal operations (recommended for production)
- **WARNING**: Important events
- **ERROR**: Error conditions
- **CRITICAL**: System failures

## Integration Options

### 1. ELK Stack (Elasticsearch + Logstash + Kibana)

**Best for:** Self-hosted, full-featured log analytics

#### Setup with Filebeat

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/log-classifier/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "log-classifier-%{+yyyy.MM.dd}"

setup.kibana:
  host: "localhost:5601"
```

#### Run Application with Log File

```bash
python server.py 2>&1 | tee /var/log/log-classifier/app.log
```

#### Kibana Dashboards

Create visualizations for:
- Request rate over time
- Error rate by endpoint
- Classification method distribution (Regex/BERT/LLM)
- Average processing time
- Top error messages

### 2. AWS CloudWatch Logs

**Best for:** AWS-hosted applications

#### Install CloudWatch Agent

```bash
pip install watchtower
```

#### Modify logger_config.py

```python
import watchtower
import boto3

# Add CloudWatch handler
cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group="/aws/log-classifier",
    stream_name="production",
    boto3_client=boto3.client('logs', region_name='us-east-1')
)
cloudwatch_handler.setFormatter(json_formatter)
logger.addHandler(cloudwatch_handler)
```

#### Run with Stdout Capture

```bash
# AWS ECS/Fargate automatically captures stdout to CloudWatch
python server.py
```

#### CloudWatch Insights Queries

```sql
-- Error rate
fields @timestamp, level, message, error
| filter level = "ERROR"
| stats count() by bin(5m)

-- Slow requests
fields @timestamp, duration_ms, path, method
| filter duration_ms > 1000
| sort duration_ms desc
| limit 20

-- Classification methods
fields @timestamp, method
| stats count() by method
```

### 3. Azure Application Insights

**Best for:** Azure-hosted applications

#### Install SDK

```bash
pip install opencensus-ext-azure
```

#### Configure in server.py

```python
from opencensus.ext.azure.log_exporter import AzureLogHandler

# Add to logger setup
logger.addHandler(AzureLogHandler(
    connection_string='InstrumentationKey=your-key-here'
))
```

#### Azure Portal

View metrics in:
- Application Insights → Logs
- Performance → Dependencies
- Failures → Exceptions
- Metrics → Custom Metrics

### 4. Datadog

**Best for:** Full-stack observability with APM

#### Install Datadog Agent

```bash
# Install agent
DD_API_KEY=<your-key> bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"

# Configure log collection
# /etc/datadog-agent/conf.d/python.d/conf.yaml
logs:
  - type: file
    path: /var/log/log-classifier/*.log
    service: log-classifier
    source: python
    sourcecategory: sourcecode
```

#### Run with Logging

```bash
python server.py 2>&1 | tee /var/log/log-classifier/app.log
```

#### Datadog Features

- **APM Tracing**: Automatic request tracing
- **Log Analytics**: Parse and search JSON logs
- **Alerting**: Set up monitors for error rates
- **Dashboards**: Pre-built Python dashboards

### 5. Splunk

**Best for:** Enterprise log management

#### Splunk Universal Forwarder

```bash
# inputs.conf
[monitor:///var/log/log-classifier/*.log]
disabled = false
sourcetype = _json
index = main

# props.conf
[_json]
INDEXED_EXTRACTIONS = json
KV_MODE = none
```

#### Run Application

```bash
python server.py 2>&1 | tee /var/log/log-classifier/app.log
```

#### Splunk Queries

```spl
# Error trends
index=main sourcetype=_json level=ERROR
| timechart count by error

# Request performance
index=main sourcetype=_json path=*
| stats avg(duration_ms) by path
| sort -avg(duration_ms)

# Classification accuracy
index=main sourcetype=_json method=*
| stats count by method
```

### 6. Grafana + Loki

**Best for:** Lightweight, cost-effective monitoring

#### Loki Configuration

```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: log-classifier
    static_configs:
      - targets:
          - localhost
        labels:
          job: log-classifier
          __path__: /var/log/log-classifier/*.log
```

#### Docker Compose

```yaml
version: "3"
services:
  log-classifier:
    build: .
    ports:
      - "8000:8000"
    logging:
      driver: json-file

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
```

#### Grafana Queries (LogQL)

```logql
# Error rate
sum(rate({job="log-classifier"} |= "ERROR" [5m]))

# Request latency
avg_over_time({job="log-classifier"} | json | duration_ms [5m])

# Classification distribution
sum by(method) (count_over_time({job="log-classifier"} | json | method != "" [1h]))
```

## Custom Metrics

### Built-in Metrics Endpoint

Access runtime metrics at: `GET /metrics`

```json
{
  "uptime_seconds": 3600,
  "total_requests": 1234,
  "classifications": {
    "regex": 800,
    "bert": 400,
    "llm": 34
  },
  "avg_processing_time_ms": {
    "regex": 1.2,
    "bert": 52.4,
    "llm": 305.8
  },
  "error_rate": 0.02
}
```

### Prometheus Integration

Add prometheus_client for metrics export:

```bash
pip install prometheus-client
```

```python
# Add to server.py
from prometheus_client import Counter, Histogram, make_asgi_app

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/prometheus-metrics", metrics_app)
```

## Alerting

### Recommended Alerts

1. **High Error Rate**
   - Condition: Error rate > 5% over 5 minutes
   - Action: Page on-call engineer

2. **Slow Response Time**
   - Condition: P95 latency > 5 seconds
   - Action: Notify team channel

3. **LLM API Failures**
   - Condition: LLM error rate > 10%
   - Action: Check API key and quota

4. **High Memory Usage**
   - Condition: Memory > 90%
   - Action: Scale up or restart

5. **Rate Limit Triggers**
   - Condition: 429 responses > 50 per minute
   - Action: Investigate potential attack

## Log Retention

### Development
- Retain: 7 days
- Storage: Local files

### Production
- Retain: 30-90 days (compliance requirements)
- Storage: Centralized log aggregation
- Archive: S3/Blob Storage for long-term

## Best Practices

1. **Structured Logging**
   - Always use JSON format
   - Include request IDs for tracing
   - Add contextual fields (user_id, session_id)

2. **Log Levels**
   - DEBUG: Development only
   - INFO: Normal operations
   - WARNING: Potential issues
   - ERROR: Failures requiring attention
   - CRITICAL: System-wide failures

3. **Sensitive Data**
   - Never log passwords or API keys
   - Mask PII (emails, phone numbers)
   - Sanitize user input in logs

4. **Performance**
   - Use async logging handlers
   - Rotate logs daily
   - Compress old logs

5. **Monitoring**
   - Track key business metrics
   - Set up dashboards for visibility
   - Configure alerts for critical issues

## Troubleshooting

### No Logs Appearing

```bash
# Check log level
echo $LOG_LEVEL

# Verify stdout
python server.py 2>&1 | head -n 10

# Check file permissions
ls -la /var/log/log-classifier/
```

### High Log Volume

```python
# Reduce verbosity
LOG_LEVEL=WARNING

# Disable debug logs in production
DEBUG=False
```

### Missing Context

```python
# Add custom fields to logger
logger.info("Event occurred", extra={
    "user_id": user_id,
    "feature_flag": "new_ui",
    "custom_metric": 123
})
```

## Sample Dashboard

### Key Metrics to Track

| Metric | Visualization | Threshold |
|--------|---------------|-----------|
| Request Rate | Line chart | - |
| Error Rate | Line chart | < 1% |
| P95 Latency | Line chart | < 1000ms |
| Classification Method | Pie chart | - |
| Top Errors | Table | - |
| Active Users | Gauge | - |

### Sample Grafana JSON

Available in: `monitoring/grafana-dashboard.json`

## Support

For monitoring setup issues:
- Check [PRODUCTION.md](PRODUCTION.md) for deployment guide
- Review [README.md](README.md) for configuration
- Open GitHub issue with log samples
