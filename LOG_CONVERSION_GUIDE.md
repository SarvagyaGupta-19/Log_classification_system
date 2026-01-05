# Log Conversion Guide

## Converting Raw Logs to CSV Format

The system requires CSV files with two columns: `source` and `log_message`. Use the included converter tool to transform your raw log files.

## Quick Start

```bash
# Basic conversion (plain text logs)
python log_converter.py your_logs.txt output.csv

# With specific format
python log_converter.py system.log output.csv --format timestamped --source server01
```

## Supported Log Formats

### 1. Plain Text (Default)
**Example input:**
```
Connection established
User login successful
Error: Database timeout
```

**Command:**
```bash
python log_converter.py app.log output.csv --format plain --source myapp
```

### 2. Timestamped Logs
**Example input:**
```
2024-01-15 10:30:45 - Connection established
[2024-01-15 10:30:46] User login successful
2024/01/15 10:30:47: Error: Database timeout
```

**Command:**
```bash
python log_converter.py system.log output.csv --format timestamped --source system
```

### 3. Syslog Format
**Example input:**
```
Jan 15 10:30:45 myserver sshd[1234]: Connection from 192.168.1.100
Jan 15 10:30:46 myserver kernel: Out of memory
```

**Command:**
```bash
python log_converter.py syslog.txt output.csv --format syslog
```

### 4. JSON Logs
**Example input:**
```json
{"timestamp": "2024-01-15T10:30:45", "source": "api", "message": "Request received"}
{"timestamp": "2024-01-15T10:30:46", "source": "database", "message": "Query executed"}
```

**Command:**
```bash
python log_converter.py app.jsonl output.csv --format json
```

### 5. Apache/Nginx Access Logs
**Example input:**
```
192.168.1.100 - - [15/Jan/2024:10:30:45 +0000] "GET /index.html HTTP/1.1" 200 1234
192.168.1.101 - - [15/Jan/2024:10:30:46 +0000] "POST /api/login HTTP/1.1" 404 567
```

**Command:**
```bash
python log_converter.py access.log output.csv --format apache
```

## Manual Conversion (Excel/Spreadsheet)

If you prefer using Excel or Google Sheets:

1. **Create a new spreadsheet**
2. **Add headers:** `source` and `log_message`
3. **Fill in data:**
   - Column A (source): Where the log came from (e.g., "api", "database", "server")
   - Column B (log_message): The actual log text

**Example:**
| source   | log_message                          |
|----------|--------------------------------------|
| api      | Connection timeout                   |
| database | Query execution failed               |
| server   | High memory usage detected           |

4. **Save as CSV** (File → Save As → CSV format)

## Command-Line Options

```bash
python log_converter.py [input_file] [output_file] [options]

Options:
  --format, -f    Log format (plain, timestamped, syslog, json, apache, custom)
  --source, -s    Source name for all logs (default: filename)
  --delimiter, -d Delimiter for custom format (default: |)

Examples:
  python log_converter.py app.log output.csv
  python log_converter.py app.log output.csv --format timestamped
  python log_converter.py app.log output.csv --format plain --source production-server
```

## Tips

- **Large files:** The converter handles files of any size
- **Multiple sources:** Convert each log file separately or combine them in Excel
- **Encoding issues:** The converter automatically handles UTF-8 and common encodings
- **Empty lines:** Automatically skipped during conversion
- **Timestamps:** Automatically removed (only log message is extracted)

## What Happens Next?

After conversion:
1. Upload the CSV to the dashboard
2. System classifies each log automatically
3. Download results with severity levels
4. View analytics and insights
