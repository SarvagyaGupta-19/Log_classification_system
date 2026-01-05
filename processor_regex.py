"""
Pattern-based log classification using regex

This is the first tier in the classification waterfall, providing
ultra-fast pattern matching for common log types.

Supported Patterns:
- User Actions: login, logout, account creation
- System Notifications: backups, updates, disk operations
- File Operations: uploads, deletions
- System Events: reboots, shutdowns

Performance: <1ms per log, no external dependencies required.
"""
import re
from typing import Optional, Dict
from logger_config import get_logger
from exceptions import ClassificationError

logger = get_logger(__name__)


class RegexClassifier:
    """Regex-based log classifier with error handling"""
    
    def __init__(self):
        """Initialize regex patterns"""
        self.regex_patterns: Dict[str, str] = {
            # Critical Errors
            r"(?i)(fatal|critical|panic|catastrophic|emergency).*(error|failure|fault)": "Critical Error",
            r"(?i)(system|service|application).*(crash|down|failed|died)": "Critical Error",
            r"(?i)out of memory": "Critical Error",
            r"(?i)(database|db).*(down|unavailable|crashed)": "Critical Error",
            
            # Errors
            r"(?i)(connection|network).*(timeout|timed out|failed|refused|lost)": "Error",
            r"(?i)(query|request|operation).*(failed|error|unsuccessful)": "Error",
            r"(?i)(packet|data).*(loss|lost|dropped|corruption)": "Error",
            r"(?i)(dns|resolution|lookup).*(failed|error|timeout)": "Error",
            r"(?i)(unable to|failed to|cannot|can't).*(connect|access|load|open|read|write)": "Error",
            r"(?i)(exception|error|failure).*occurred": "Error",
            r"(?i)(500|502|503|504) (error|status)": "Error",
            r"(?i)internal server error": "Error",
            
            # Security Alerts
            r"(?i)(failed|unsuccessful).*(login|authentication|auth)": "Security Alert",
            r"(?i)(password|credential).*(reset|change|update|expired)": "Security Alert",
            r"(?i)(unauthorized|forbidden).*(access|attempt)": "Security Alert",
            r"(?i)(brute.?force|ddos|dos).*(attack|attempt|detected)": "Security Alert",
            r"(?i)(malware|virus|threat|intrusion).*(detected|found|blocked)": "Security Alert",
            r"(?i)(security|firewall).*(breach|violation|alert|warning)": "Security Alert",
            
            # Workflow Errors
            r"(?i)(workflow|pipeline|process).*(failed|error|stopped)": "Workflow Error",
            r"(?i)(job|task|batch).*(failed|error|timeout)": "Workflow Error",
            r"(?i)(validation|verification).*(failed|error)": "Workflow Error",
            
            # Deprecation Warnings
            r"(?i)(deprecated|obsolete|legacy)": "Deprecation Warning",
            r"(?i)(slow|performance).*(query|operation|response)": "Deprecation Warning",
            r"(?i)(will be removed|no longer supported)": "Deprecation Warning",
            
            # Resource Usage
            r"(?i)(memory|ram|heap).*(usage|utilization|consumption|high|low|%)": "Resource Usage",
            r"(?i)(disk|storage|space).*(usage|full|low|warning|%)": "Resource Usage",
            r"(?i)(cpu|processor).*(usage|load|high|%)": "Resource Usage",
            r"(?i)(bandwidth|network|traffic).*(usage|high|peak)": "Resource Usage",
            r"(?i)(capacity|quota|limit).*(reached|exceeded|warning)": "Resource Usage",
            
            # HTTP Status
            r"(?i)(rate limit|throttle).*(exceeded|reached)": "HTTP Status",
            r"(?i)(http|https).*(200|201|204|301|302|304|400|401|403|404)": "HTTP Status",
            r"(?i)(get|post|put|delete|patch).*(request|response)": "HTTP Status",
            
            # User Actions
            r"(?i)user.*logged (in|out)": "User Action",
            r"(?i)account.*(created|deleted|updated|activated|suspended)": "User Action",
            r"(?i)user.*(registered|signed up|signed in)": "User Action",
            r"(?i)(profile|settings).*(updated|changed|modified)": "User Action",
            
            # System Notifications
            r"(?i)backup.*(started|ended|completed|successful|failed)": "System Notification",
            r"(?i)system.*(updated|upgraded|patched|restarted|rebooted)": "System Notification",
            r"(?i)(maintenance|update).*(scheduled|started|completed)": "System Notification",
            r"(?i)file.*(uploaded|downloaded|deleted)": "System Notification",
            r"(?i)(disk cleanup|cleanup).*(started|completed|successful)": "System Notification",
            r"(?i)(service|daemon).*(started|stopped|restarted)": "System Notification",
        }
        logger.info("Regex classifier initialized", extra={"pattern_count": len(self.regex_patterns)})
    
    def classify(self, log_message: str) -> Optional[str]:
        """
        Classify log message using regex patterns
        
        Args:
            log_message: Log message to classify
            
        Returns:
            Classification label or None if no match
            
        Raises:
            ClassificationError: If classification fails
        """
        if not log_message or not isinstance(log_message, str):
            logger.warning("Invalid log message", extra={"message": str(log_message)[:100]})
            return None
        
        try:
            for pattern, label in self.regex_patterns.items():
                try:
                    if re.search(pattern, log_message):
                        logger.debug("Regex match found", extra={
                            "pattern": pattern[:50],
                            "label": label
                        })
                        return label
                except re.error as e:
                    logger.error("Regex pattern error", extra={
                        "pattern": pattern,
                        "error": str(e)
                    })
                    continue
            
            return None
            
        except Exception as e:
            logger.error("Regex classification failed", extra={
                "error": str(e),
                "message": log_message[:100]
            })
            raise ClassificationError(f"Regex classification failed: {str(e)}")


# Global instance for backward compatibility
_classifier = RegexClassifier()


def classify_with_regex(log_message: str) -> Optional[str]:
    """Legacy function for backward compatibility"""
    return _classifier.classify(log_message)

if __name__ == "__main__":
    print(classify_with_regex("Backup completed successfully."))
    print(classify_with_regex("Account with ID 1234 created by User1."))
    print(classify_with_regex("Hey Bro, chill ya!"))


