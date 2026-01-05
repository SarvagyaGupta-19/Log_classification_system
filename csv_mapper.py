"""
Generic CSV Column Mapper

Intelligently maps any CSV columns to the required format:
- source: System/service/type that generated the log
- log_message: The actual log text

Handles various column naming conventions automatically.
"""

import pandas as pd
from typing import Dict, Optional, Tuple


# Column mapping patterns (case-insensitive)
MESSAGE_COLUMNS = [
    'log_message', 'message', 'msg', 'log', 'text', 'description', 'desc',
    'content', 'body', 'detail', 'details', 'error', 'event', 'log_text',
    'logmessage', 'log_msg', 'error_message', 'event_message', 'raw_log',
    'entry', 'line', 'record', 'data', 'payload'
]

SOURCE_COLUMNS = [
    'source', 'src', 'type', 'category', 'service', 'system', 'component',
    'application', 'app', 'module', 'logger', 'facility', 'tag', 'level',
    'severity', 'priority', 'class', 'origin', 'host', 'hostname', 'server',
    'node', 'machine', 'device', 'name', 'log_type', 'event_type'
]


def find_best_column_match(columns: list, patterns: list) -> Optional[str]:
    """
    Find the best matching column from a list of patterns
    
    Args:
        columns: Available column names in CSV
        patterns: List of pattern strings to match against
    
    Returns:
        Best matching column name or None
    """
    columns_lower = [col.lower().strip() for col in columns]
    
    # First pass: exact match
    for pattern in patterns:
        if pattern in columns_lower:
            idx = columns_lower.index(pattern)
            return columns[idx]
    
    # Second pass: contains match
    for pattern in patterns:
        for i, col in enumerate(columns_lower):
            if pattern in col or col in pattern:
                return columns[i]
    
    return None


def detect_column_mappings(df: pd.DataFrame) -> Dict[str, str]:
    """
    Automatically detect and map CSV columns to required format
    
    Args:
        df: Input DataFrame
    
    Returns:
        Dictionary with mappings: {'source': 'actual_col', 'log_message': 'actual_col'}
    """
    columns = df.columns.tolist()
    mappings = {}
    
    # Find message column
    message_col = find_best_column_match(columns, MESSAGE_COLUMNS)
    if message_col:
        mappings['log_message'] = message_col
    
    # Find source column
    source_col = find_best_column_match(columns, SOURCE_COLUMNS)
    if source_col:
        mappings['source'] = source_col
    
    return mappings


def select_best_text_column(df: pd.DataFrame, exclude_cols: Optional[list] = None) -> Optional[str]:
    """
    Select the column that most likely contains text/log messages
    Based on average length and data type
    
    Args:
        df: Input DataFrame
        exclude_cols: Columns to exclude from consideration
    
    Returns:
        Best text column name or None
    """
    if exclude_cols is None:
        exclude_cols = []
    
    candidates = []
    
    for col in df.columns:
        if col in exclude_cols:
            continue
        
        # Check if column contains string data
        if df[col].dtype == 'object' or df[col].dtype == 'string':
            # Calculate average length of non-null values
            avg_length = df[col].dropna().astype(str).str.len().mean()
            
            # Prefer columns with longer text (likely to be messages)
            if avg_length > 10:  # Arbitrary threshold
                candidates.append((col, avg_length))
    
    # Return column with longest average text
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    return None


def smart_csv_mapping(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Intelligently map any CSV to required format
    
    Strategies:
    1. Look for exact or similar column names
    2. If missing message column, find the longest text column
    3. If missing source column, use filename or 'unknown'
    4. If only one column exists, use it as message with default source
    
    Args:
        df: Input DataFrame
    
    Returns:
        Tuple of (mapped DataFrame, mapping info dict)
    """
    original_columns = df.columns.tolist()
    mappings = detect_column_mappings(df)
    mapping_info = {
        'original_columns': original_columns,
        'detected_mappings': mappings.copy(),
        'warnings': [],
        'auto_assigned': []
    }
    
    # Create a new DataFrame with required columns
    result_df = pd.DataFrame()
    
    # Handle log_message column
    if 'log_message' in mappings:
        result_df['log_message'] = df[mappings['log_message']].fillna('').astype(str)
        mapping_info['message_source'] = f"Mapped from '{mappings['log_message']}'"
    else:
        # Try to find the best text column
        text_col = select_best_text_column(df, exclude_cols=list(mappings.values()))
        
        if text_col:
            result_df['log_message'] = df[text_col].fillna('').astype(str)
            mapping_info['message_source'] = f"Auto-detected from '{text_col}' (longest text column)"
            mapping_info['auto_assigned'].append('log_message')
        elif len(df.columns) == 1:
            # Single column CSV - use it as message
            result_df['log_message'] = df.iloc[:, 0].fillna('').astype(str)
            mapping_info['message_source'] = f"Using only column '{df.columns[0]}'"
            mapping_info['auto_assigned'].append('log_message')
        else:
            # Fallback: concatenate all columns (fill NaN first)
            result_df['log_message'] = df.fillna('').apply(lambda row: ' | '.join(row.astype(str).values), axis=1)
            mapping_info['message_source'] = "Concatenated all columns"
            mapping_info['warnings'].append("No clear message column found - concatenated all data")
            mapping_info['auto_assigned'].append('log_message')
    
    # Handle source column
    if 'source' in mappings:
        result_df['source'] = df[mappings['source']].fillna('unknown').astype(str)
        mapping_info['source_source'] = f"Mapped from '{mappings['source']}'"
    else:
        # Try to find any categorical column
        categorical_col = None
        for col in df.columns:
            if col not in mappings.values() and df[col].dtype == 'object':
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio < 0.3:  # Less than 30% unique values (likely categorical)
                    categorical_col = col
                    break
        
        if categorical_col:
            result_df['source'] = df[categorical_col].fillna('unknown').astype(str)
            mapping_info['source_source'] = f"Auto-detected from '{categorical_col}' (categorical data)"
            mapping_info['auto_assigned'].append('source')
        else:
            # Use default source
            result_df['source'] = 'unknown'
            mapping_info['source_source'] = "Default 'unknown' (no source column found)"
            mapping_info['warnings'].append("No source column detected - using 'unknown'")
            mapping_info['auto_assigned'].append('source')
    
    # Clean up: replace 'nan' strings that came from NaN values
    result_df['log_message'] = result_df['log_message'].replace('nan', '')
    result_df['source'] = result_df['source'].replace('nan', 'unknown')
    
    # Remove empty rows (including whitespace-only)
    initial_rows = len(result_df)
    result_df = result_df[result_df['log_message'].str.strip() != '']
    removed_rows = initial_rows - len(result_df)
    
    if removed_rows > 0:
        mapping_info['warnings'].append(f"Removed {removed_rows} empty rows")
    
    mapping_info['final_row_count'] = len(result_df)
    
    return result_df, mapping_info


def format_mapping_summary(mapping_info: Dict) -> str:
    """
    Create a human-readable summary of the column mapping
    
    Args:
        mapping_info: Mapping information dictionary
    
    Returns:
        Formatted summary string
    """
    lines = ["CSV Column Mapping Summary:"]
    lines.append("-" * 50)
    lines.append(f"Original columns: {', '.join(mapping_info['original_columns'])}")
    lines.append("")
    lines.append(f"✓ log_message: {mapping_info['message_source']}")
    lines.append(f"✓ source: {mapping_info['source_source']}")
    
    if mapping_info['auto_assigned']:
        lines.append("")
        lines.append(f"Auto-assigned: {', '.join(mapping_info['auto_assigned'])}")
    
    if mapping_info['warnings']:
        lines.append("")
        lines.append("Warnings:")
        for warning in mapping_info['warnings']:
            lines.append(f"  ⚠ {warning}")
    
    lines.append("")
    lines.append(f"Total rows processed: {mapping_info['final_row_count']}")
    
    return "\n".join(lines)
