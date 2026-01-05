"""
Log File Converter - Convert raw log files to CSV format

Supports multiple log formats:
- Plain text logs (one log per line)
- Timestamped logs
- Syslog format
- JSON logs
- Custom delimited logs

Usage:
    python log_converter.py input.log output.csv --format plain
    python log_converter.py input.log output.csv --format syslog
    python log_converter.py input.log output.csv --format json
"""

import pandas as pd
import re
import json
import argparse
from pathlib import Path
from datetime import datetime


def parse_plain_text(file_path, source_name):
    """
    Parse plain text logs (one log per line)
    
    Example:
        Connection established
        User login successful
        Error: Database timeout
    """
    logs = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:  # Skip empty lines
                logs.append({
                    'source': source_name,
                    'log_message': line
                })
    return logs


def parse_timestamped_logs(file_path, source_name):
    """
    Parse logs with timestamps at the beginning
    
    Example:
        2024-01-15 10:30:45 - Connection established
        [2024-01-15 10:30:46] User login successful
        2024/01/15 10:30:47: Error: Database timeout
    """
    logs = []
    # Pattern to match common timestamp formats
    timestamp_pattern = r'^[\[\(]?\d{4}[-/]\d{2}[-/]\d{2}[\s\]\)]*[\[\(]?\d{1,2}:\d{2}:\d{2}[\]\)]?[\s:-]*'
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line:
                # Remove timestamp if present
                message = re.sub(timestamp_pattern, '', line).strip()
                if message:
                    logs.append({
                        'source': source_name,
                        'log_message': message
                    })
    return logs


def parse_syslog(file_path, source_name=None):
    """
    Parse syslog format
    
    Example:
        Jan 15 10:30:45 myserver sshd[1234]: Connection from 192.168.1.100
        Jan 15 10:30:46 myserver kernel: Out of memory
    """
    logs = []
    # Syslog pattern: Month Day Time Hostname Process: Message
    syslog_pattern = r'^(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[\d+\])?\s*:\s*(.+)'
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line:
                match = re.match(syslog_pattern, line)
                if match:
                    _, hostname, process, message = match.groups()
                    logs.append({
                        'source': source_name or process,
                        'log_message': message.strip()
                    })
                else:
                    # Fallback if pattern doesn't match
                    logs.append({
                        'source': source_name or 'unknown',
                        'log_message': line
                    })
    return logs


def parse_json_logs(file_path, source_field='source', message_field='message'):
    """
    Parse JSON logs (one JSON object per line)
    
    Example:
        {"timestamp": "2024-01-15T10:30:45", "source": "api", "message": "Request received"}
        {"timestamp": "2024-01-15T10:30:46", "source": "database", "message": "Query executed"}
    """
    logs = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    logs.append({
                        'source': data.get(source_field, 'unknown'),
                        'log_message': data.get(message_field, str(data))
                    })
                except json.JSONDecodeError:
                    print(f"Warning: Line {line_num} is not valid JSON, skipping")
    return logs


def parse_apache_logs(file_path, source_name='apache'):
    """
    Parse Apache/Nginx access logs
    
    Example:
        192.168.1.100 - - [15/Jan/2024:10:30:45 +0000] "GET /index.html HTTP/1.1" 200 1234
    """
    logs = []
    # Basic Apache log pattern
    apache_pattern = r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\S+)'
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line:
                match = re.match(apache_pattern, line)
                if match:
                    ip, timestamp, request, status, size = match.groups()
                    logs.append({
                        'source': source_name,
                        'log_message': f"{status} {request} from {ip}"
                    })
                else:
                    logs.append({
                        'source': source_name,
                        'log_message': line
                    })
    return logs


def parse_custom_delimited(file_path, delimiter='|', source_col=0, message_col=1):
    """
    Parse custom delimited logs
    
    Example (pipe-delimited):
        api|Connection established
        database|Query timeout
    """
    logs = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(delimiter)
                if len(parts) > max(source_col, message_col):
                    logs.append({
                        'source': parts[source_col].strip(),
                        'log_message': parts[message_col].strip()
                    })
    return logs


def convert_log_to_csv(input_file, output_file, log_format='plain', source_name=None):
    """
    Convert log file to CSV format
    
    Args:
        input_file: Path to input log file
        output_file: Path to output CSV file
        log_format: Format of the log file (plain, timestamped, syslog, json, apache, custom)
        source_name: Source name to use (default: filename)
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Default source name is the filename without extension
    if source_name is None:
        source_name = input_path.stem
    
    print(f"Converting {input_file} to CSV format...")
    print(f"Format: {log_format}")
    print(f"Source: {source_name}")
    
    # Parse based on format
    if log_format == 'plain':
        logs = parse_plain_text(input_file, source_name)
    elif log_format == 'timestamped':
        logs = parse_timestamped_logs(input_file, source_name)
    elif log_format == 'syslog':
        logs = parse_syslog(input_file, source_name)
    elif log_format == 'json':
        logs = parse_json_logs(input_file)
    elif log_format == 'apache':
        logs = parse_apache_logs(input_file, source_name)
    elif log_format == 'custom':
        logs = parse_custom_delimited(input_file)
    else:
        raise ValueError(f"Unsupported format: {log_format}")
    
    if not logs:
        raise ValueError("No logs found in input file")
    
    # Convert to DataFrame and save
    df = pd.DataFrame(logs)
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Conversion complete!")
    print(f"   Total logs: {len(logs)}")
    print(f"   Output file: {output_file}")
    print(f"\nSample rows:")
    print(df.head(3).to_string(index=False))
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Convert raw log files to CSV format for classification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plain text logs
  python log_converter.py app.log output.csv --format plain --source myapp
  
  # Timestamped logs
  python log_converter.py system.log output.csv --format timestamped
  
  # Syslog format
  python log_converter.py syslog.txt output.csv --format syslog
  
  # JSON logs
  python log_converter.py app.jsonl output.csv --format json
  
  # Apache logs
  python log_converter.py access.log output.csv --format apache

Supported formats:
  plain       - One log per line (default)
  timestamped - Logs with timestamps (automatically removed)
  syslog      - Standard syslog format
  json        - One JSON object per line
  apache      - Apache/Nginx access logs
  custom      - Custom delimited (use --delimiter option)
        """
    )
    
    parser.add_argument('input', help='Input log file path')
    parser.add_argument('output', help='Output CSV file path')
    parser.add_argument('--format', '-f', 
                       choices=['plain', 'timestamped', 'syslog', 'json', 'apache', 'custom'],
                       default='plain',
                       help='Log file format (default: plain)')
    parser.add_argument('--source', '-s', 
                       help='Source name for logs (default: input filename)')
    parser.add_argument('--delimiter', '-d',
                       default='|',
                       help='Delimiter for custom format (default: |)')
    
    args = parser.parse_args()
    
    try:
        convert_log_to_csv(
            args.input,
            args.output,
            args.format,
            args.source
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
