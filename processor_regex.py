"""Pattern-based log classification using regex"""
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
            r"User User\d+ logged (in|out).": "User Action",
            r"Backup (started|ended) at .*": "System Notification",
            r"Backup completed successfully.": "System Notification",
            r"System updated to version .*": "System Notification",
            r"File .* uploaded successfully by user .*": "System Notification",
            r"Disk cleanup completed successfully.": "System Notification",
            r"System reboot initiated by user .*": "System Notification",
            r"Account with ID .* created by .*": "User Action"
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


