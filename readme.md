# Log Classification System

> Enterprise-grade log classification and severity analysis system powered by machine learning

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

### Intelligent Classification
- **Multi-stage ML Pipeline**: Regex → BERT → LLM fallback architecture
- **42+ Regex Patterns**: Ultra-fast pattern matching for common log types
- **BERT Model**: 99.63% accuracy on log classification
- **Groq LLM Integration**: Advanced classification for edge cases

### Universal Format Support
- **Auto-detect CSV Columns**: Recognizes 20+ message patterns, 25+ source patterns
- **Multiple File Formats**: CSV, LOG, TXT, JSON/JSONL
- **Automatic Conversion**: Plain text, timestamped, syslog, JSON logs → classified results
- **Encoding Support**: UTF-8, Latin-1, ISO-8859-1, CP1252, UTF-16

### Severity Analysis
- **6 Severity Levels**: CRITICAL, HIGH, MEDIUM, LOW, INFO, UNCLASSIFIED
- **Real-time Analytics**: Interactive dashboard with severity breakdown
- **Category Distribution**: Top categories with counts
- **Visual Indicators**: Color-coded severity icons (🔴🟠🟡🟢🔵⚪)

### Professional Web Interface
- **Modern UI/UX**: Clean, professional enterprise design
- **Drag & Drop Upload**: Intuitive file handling
- **Real-time Progress**: Animated classification progress
- **Mobile Responsive**: Works on all devices
- **Download Results**: CSV export with classifications

### Enterprise Features
- **Health Monitoring**: `/health` and `/metrics` endpoints
- **Request Logging**: Structured JSON logs with request IDs
- **Error Handling**: Comprehensive validation and error messages
- **Performance Metrics**: Track processing time and accuracy
- **API Documentation**: Auto-generated Swagger UI

## 📋 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/log-classification-system.git
cd log-classification-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
GROQ_API_KEY=your_groq_api_key_here
LOG_LEVEL=INFO
ENVIRONMENT=production
```

4. **Run the server**
```bash
python server.py
```

5. **Access the dashboard**
```
Open http://localhost:8000 in your browser
```

## 🎯 Usage

### Web Interface

1. **Open Dashboard**: Navigate to `http://localhost:8000`
2. **Upload File**: Drag & drop or browse for your log file
   - Supports: `.csv`, `.log`, `.txt`, `.json`, `.jsonl`
3. **Automatic Processing**: System detects format and classifies logs
4. **View Analytics**: See severity breakdown and category distribution
5. **Download Results**: Get classified logs with severity levels

### Command-Line Conversion

Convert raw log files to CSV before upload:

```bash
# Plain text logs
python log_converter.py app.log output.csv --format plain

# Timestamped logs
python log_converter.py system.log output.csv --format timestamped

# JSON logs
python log_converter.py app.jsonl output.csv --format json

# Syslog format
python log_converter.py syslog.txt output.csv --format syslog
```

### API Endpoints

#### Classification
```bash
POST /classify/
Content-Type: multipart/form-data

# Upload any supported file format
curl -X POST -F "file=@logs.csv" http://localhost:8000/classify/
```

#### Health Check
```bash
GET /health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "classification_engine": "healthy",
    "secondary_classifier": "healthy",
    "file_system": "healthy"
  }
}
```

#### Metrics
```bash
GET /metrics

# Response
{
  "total_classifications": 1250,
  "classifications_by_method": {
    "regex": 450,
    "bert": 720,
    "llm": 80
  },
  "average_processing_time_ms": 125.5,
  "error_rate": 0.02,
  "uptime_seconds": 3600
}
```

## 📊 Classification Categories

| Category | Severity | Description |
|----------|----------|-------------|
| Critical Error | CRITICAL 🔴 | System-breaking errors requiring immediate action |
| Error | HIGH 🟠 | Significant issues needing urgent attention |
| Security Alert | HIGH 🟠 | Authentication failures, security breaches |
| Workflow Error | MEDIUM 🟡 | Process failures requiring investigation |
| Deprecation Warning | MEDIUM 🟡 | Slow queries, deprecated features |
| HTTP Status | LOW 🟢 | Rate limits, HTTP status codes |
| Resource Usage | INFO 🔵 | Memory, CPU, disk space metrics |
| System Notification | INFO 🔵 | Backups, updates, system events |
| User Action | INFO 🔵 | Login, logout, account operations |
| Unclassified | UNCLASSIFIED ⚪ | Logs requiring manual review |

## 🏗️ Architecture

```
┌─────────────────┐
│   Web Upload    │
│  (Any Format)   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Format Detect  │
│  & Convert CSV  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Smart Column   │
│    Mapping      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Regex Patterns  │──────> Match? ──> Category
│   (42 rules)    │          │
└─────────────────┘          │ No match
                             v
                    ┌─────────────────┐
                    │   BERT Model    │──> 99.6% Accuracy
                    │   (MiniLM-L6)   │
                    └────────┬────────┘
                             │ Low confidence
                             v
                    ┌─────────────────┐
                    │   Groq LLM      │──> Advanced Analysis
                    │ (llama-3.3-70b) │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │  Severity Map   │
                    │  & Analytics    │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │  CSV Export +   │
                    │   Dashboard     │
                    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key for LLM fallback | Required |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING) | INFO |
| `ENVIRONMENT` | Environment (development/production) | production |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | 50 |
| `BERT_MODEL` | Sentence transformer model | all-MiniLM-L6-v2 |

### Settings (config.py)

```python
app_name = "Log Classification System"
app_version = "1.0.0"
max_file_size_mb = 50
resources_dir = "resources"
output_file = "resources/output.csv"
```

## 📁 Project Structure

```
Log_classification_system/
├── server.py                 # FastAPI server
├── classify.py              # Classification orchestrator
├── config.py                # Configuration settings
├── csv_mapper.py            # Auto column detection
├── log_converter.py         # Format conversion CLI
├── processor_regex.py       # Regex classifier (42 patterns)
├── processor_bert.py        # BERT classifier
├── processor_llm.py         # Groq LLM classifier
├── severity_mapper.py       # Severity level mapping
├── visualization.py         # Analytics generation
├── models.py                # Pydantic models
├── exceptions.py            # Custom exceptions
├── logger_config.py         # Logging configuration
├── metrics.py               # Performance metrics
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── LICENSE                  # MIT License
├── README.md               # This file
├── templates/
│   └── dashboard.html      # Web interface
├── static/
│   ├── css/
│   │   └── dashboard.css   # Styles
│   └── js/
│       └── dashboard.js    # Frontend logic
├── models/
│   └── log_classifier.joblib  # BERT model (99.6% accuracy)
└── resources/
    └── test_logs.log       # Sample log file
```

## 🧪 Testing

### Sample Files Included

- `resources/test_logs.log` - Timestamped logs with mixed severities
- `Model_training/dataset/synthetic_logs.csv` - Training dataset

### Run Tests

```bash
# Upload test file
curl -X POST -F "file=@resources/test_logs.log" http://localhost:8000/classify/

# Check health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics
```

## 🚀 Performance

- **Regex Classification**: < 1ms per log
- **BERT Classification**: ~50ms per log
- **LLM Fallback**: ~200ms per log
- **Overall Accuracy**: 99.63%
- **Throughput**: 1000+ logs/minute

## 🛠️ Development

### Adding New Patterns

Edit `processor_regex.py`:

```python
self.regex_patterns: Dict[str, str] = {
    r"(?i)your_pattern_here": "Your Category",
    # Add more patterns...
}
```

### Adding New Severity Levels

Edit `severity_mapper.py`:

```python
class SeverityLevel(str, Enum):
    YOUR_LEVEL = "YOUR_LEVEL"

CATEGORY_SEVERITY_MAP = {
    "Your Category": SeverityLevel.YOUR_LEVEL,
}
```

## 📝 API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework
- **Sentence Transformers** - BERT model for classification
- **Groq** - LLM API integration
- **Pandas** - Data processing
- **Font Awesome** - UI icons

## 📧 Support

For issues, questions, or contributions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/log-classification-system/issues)
- Documentation: See [LOG_CONVERSION_GUIDE.md](LOG_CONVERSION_GUIDE.md)

---

**Built with ❤️ for enterprise log management**
