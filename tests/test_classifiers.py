"""
Unit Tests for Log Classification System
Owner: QA Engineer
Critical: Test coverage for all components
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from processor_regex import RegexClassifier
from models import LogEntry, ClassificationMethod
from exceptions import ClassificationError


class TestRegexClassifier:
    """Test regex classifier"""
    
    def test_user_action_classification(self):
        """Test user action patterns"""
        classifier = RegexClassifier()
        
        result = classifier.classify("User User123 logged in.")
        assert result == "User Action"
        
        result = classifier.classify("User User456 logged out.")
        assert result == "User Action"
    
    def test_system_notification(self):
        """Test system notification patterns"""
        classifier = RegexClassifier()
        
        result = classifier.classify("Backup started at 2024-01-01 00:00:00")
        assert result == "System Notification"
        
        result = classifier.classify("System updated to version 2.0")
        assert result == "System Notification"
    
    def test_no_match(self):
        """Test unmatched patterns"""
        classifier = RegexClassifier()
        
        result = classifier.classify("Random log message")
        assert result is None
    
    def test_empty_message(self):
        """Test empty message handling"""
        classifier = RegexClassifier()
        
        result = classifier.classify("")
        assert result is None
        
        # Test with non-string type (should handle gracefully)
        result = classifier.classify("   ")  # whitespace only
        assert result is None


class TestLogEntry:
    """Test Pydantic models"""
    
    def test_valid_log_entry(self):
        """Test valid log entry creation"""
        entry = LogEntry(
            source="WebServer",
            log_message="Test message"
        )
        assert entry.source == "WebServer"
        assert entry.log_message == "Test message"
    
    def test_empty_message_validation(self):
        """Test empty message validation"""
        with pytest.raises(ValueError):
            LogEntry(source="Test", log_message="")
    
    def test_whitespace_trimming(self):
        """Test message trimming"""
        entry = LogEntry(
            source="Test",
            log_message="  Test message  "
        )
        assert entry.log_message == "Test message"


class TestClassificationMethod:
    """Test classification method enum"""
    
    def test_enum_values(self):
        """Test enum has correct values"""
        assert ClassificationMethod.REGEX.value == "regex"
        assert ClassificationMethod.BERT.value == "bert"
        assert ClassificationMethod.LLM.value == "llm"
        assert ClassificationMethod.UNCLASSIFIED.value == "unclassified"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
