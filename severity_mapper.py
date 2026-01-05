"""
Severity Mapper - Maps log categories to severity levels and priorities

This module provides severity classification for log categories to enable
better visualization, alerting, and prioritization of log analysis.

Severity Levels:
- CRITICAL: System-breaking errors requiring immediate action
- HIGH: Significant issues needing urgent attention
- MEDIUM: Notable issues requiring investigation
- LOW: Minor issues or informational
- INFO: Normal operations and informational logs
"""
from enum import Enum
from typing import Dict, Tuple


class SeverityLevel(str, Enum):
    """Severity levels for log categories"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    UNCLASSIFIED = "UNCLASSIFIED"


# Category to Severity Mapping
CATEGORY_SEVERITY_MAP: Dict[str, SeverityLevel] = {
    # Critical severity - System breaking errors
    "Critical Error": SeverityLevel.CRITICAL,
    
    # High severity - Security and operational errors
    "Error": SeverityLevel.HIGH,
    "Security Alert": SeverityLevel.HIGH,
    
    # Medium severity - Issues requiring investigation
    "Workflow Error": SeverityLevel.MEDIUM,
    "Deprecation Warning": SeverityLevel.MEDIUM,
    
    # Low severity - Minor issues
    "HTTP Status": SeverityLevel.LOW,
    
    # Info - Normal operations
    "System Notification": SeverityLevel.INFO,
    "User Action": SeverityLevel.INFO,
    "Resource Usage": SeverityLevel.INFO,
    
    # Fallback
    "Unclassified": SeverityLevel.UNCLASSIFIED,
}


# Severity to Color Mapping (for visualizations)
SEVERITY_COLORS: Dict[SeverityLevel, str] = {
    SeverityLevel.CRITICAL: "#DC143C",  # Crimson Red
    SeverityLevel.HIGH: "#FF8C00",      # Dark Orange
    SeverityLevel.MEDIUM: "#FFD700",    # Gold
    SeverityLevel.LOW: "#32CD32",       # Lime Green
    SeverityLevel.INFO: "#4169E1",      # Royal Blue
    SeverityLevel.UNCLASSIFIED: "#9CA3AF",  # Gray
}


# Severity to Priority Score (for sorting)
SEVERITY_PRIORITY: Dict[SeverityLevel, int] = {
    SeverityLevel.CRITICAL: 5,
    SeverityLevel.HIGH: 4,
    SeverityLevel.MEDIUM: 3,
    SeverityLevel.LOW: 2,
    SeverityLevel.INFO: 1,
    SeverityLevel.UNCLASSIFIED: 0,
}


# Severity to Icon/Emoji (for display)
SEVERITY_ICONS: Dict[SeverityLevel, str] = {
    SeverityLevel.CRITICAL: "🔴",
    SeverityLevel.HIGH: "🟠",
    SeverityLevel.MEDIUM: "🟡",
    SeverityLevel.LOW: "🟢",
    SeverityLevel.INFO: "🔵",
    SeverityLevel.UNCLASSIFIED: "⚪",
}


def get_severity(category: str) -> SeverityLevel:
    """
    Get severity level for a log category
    
    Args:
        category: Log category name
        
    Returns:
        SeverityLevel enum value
    """
    return CATEGORY_SEVERITY_MAP.get(category, SeverityLevel.LOW)


def get_severity_color(severity: SeverityLevel) -> str:
    """Get hex color code for severity level"""
    return SEVERITY_COLORS.get(severity, "#808080")


def get_severity_priority(severity: SeverityLevel) -> int:
    """Get numeric priority for severity level (higher = more severe)"""
    return SEVERITY_PRIORITY.get(severity, 0)


def get_severity_icon(severity: SeverityLevel) -> str:
    """Get icon/emoji for severity level"""
    return SEVERITY_ICONS.get(severity, "⚪")


def get_category_info(category: str) -> Tuple[SeverityLevel, str, int, str]:
    """
    Get complete severity information for a category
    
    Args:
        category: Log category name
        
    Returns:
        Tuple of (severity, color, priority, icon)
    """
    severity = get_severity(category)
    return (
        severity,
        get_severity_color(severity),
        get_severity_priority(severity),
        get_severity_icon(severity)
    )


def get_severity_distribution(categories: list) -> Dict[str, int]:
    """
    Calculate severity distribution from list of categories
    
    Args:
        categories: List of category names
        
    Returns:
        Dictionary mapping severity level to count
    """
    distribution = {level.value: 0 for level in SeverityLevel}
    
    for category in categories:
        severity = get_severity(category)
        distribution[severity.value] += 1
    
    return distribution


def get_severity_stats(categories: list) -> Dict:
    """
    Get comprehensive severity statistics
    
    Args:
        categories: List of category names
        
    Returns:
        Dictionary with severity statistics and percentages
    """
    total = len(categories)
    if total == 0:
        return {}
    
    distribution = get_severity_distribution(categories)
    
    stats = {
        "total_logs": total,
        "severity_counts": distribution,
        "severity_percentages": {
            level: round((count / total) * 100, 2)
            for level, count in distribution.items()
        },
        "critical_count": distribution.get(SeverityLevel.CRITICAL.value, 0),
        "high_priority_count": (
            distribution.get(SeverityLevel.CRITICAL.value, 0) +
            distribution.get(SeverityLevel.HIGH.value, 0)
        ),
        "requires_attention": (
            distribution.get(SeverityLevel.CRITICAL.value, 0) +
            distribution.get(SeverityLevel.HIGH.value, 0) +
            distribution.get(SeverityLevel.MEDIUM.value, 0)
        )
    }
    
    return stats


def categorize_by_severity(logs_df) -> Dict[str, list]:
    """
    Group logs by severity level
    
    Args:
        logs_df: DataFrame with 'target_label' column
        
    Returns:
        Dictionary mapping severity level to list of log indices
    """
    severity_groups = {level.value: [] for level in SeverityLevel}
    
    for idx, category in enumerate(logs_df['target_label']):
        severity = get_severity(category)
        severity_groups[severity.value].append(idx)
    
    return severity_groups


if __name__ == "__main__":
    # Test the severity mapper
    print("=" * 70)
    print("SEVERITY MAPPER TEST")
    print("=" * 70)
    
    # Test all categories
    test_categories = [
        "Critical Error",
        "Error",
        "Security Alert",
        "Workflow Error",
        "Deprecation Warning",
        "HTTP Status",
        "System Notification",
        "User Action",
        "Resource Usage",
    ]
    
    print("\nCategory Severity Mapping:")
    print("-" * 70)
    for category in test_categories:
        severity, color, priority, icon = get_category_info(category)
        print(f"{icon} {category:25s} → {severity.value:10s} (Priority: {priority}, Color: {color})")
    
    # Test distribution
    print("\n" + "=" * 70)
    print("SEVERITY DISTRIBUTION TEST")
    print("=" * 70)
    
    sample_logs = [
        "Critical Error", "Critical Error",
        "Security Alert", "Security Alert", "Security Alert",
        "Error",
        "HTTP Status", "HTTP Status", "HTTP Status", "HTTP Status",
        "System Notification", "System Notification",
    ]
    
    stats = get_severity_stats(sample_logs)
    print(f"\nTotal Logs: {stats['total_logs']}")
    print("\nSeverity Breakdown:")
    for severity, count in stats['severity_counts'].items():
        pct = stats['severity_percentages'][severity]
        print(f"  {severity:10s}: {count:3d} ({pct:5.1f}%)")
    
    print(f"\nCritical Logs: {stats['critical_count']}")
    print(f"High Priority (Critical + High): {stats['high_priority_count']}")
    print(f"Requires Attention (C+H+M): {stats['requires_attention']}")
    
    print("\n" + "=" * 70)
