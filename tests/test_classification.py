import pytest
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classify import classify_log
from models import ClassificationMethod

class TestLogClassification:
    def test_regex_classification(self):
        """Test that simple patterns are caught by regex"""
        log = "127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] \"GET /api/v1/users HTTP/1.1\" 200 2326"
        result = classify_log("WebServer", log)
        assert result["method"] == ClassificationMethod.REGEX
        assert result["category"] is not None
        assert result["confidence"] > 0.9

    def test_bert_classification_fallback(self):
        """Test that complex logs fall back to BERT (mocking might be needed for full isolation)"""
        # This log is unlikely option for regex, should hit BERT
        log = "The fundamental problem with the upstream dependency caused a cascade failure."
        result = classify_log("Application", log)
        # It could be BERT or LLM depending on config, but definitely not Regex usually
        assert result["method"] in [ClassificationMethod.BERT, ClassificationMethod.LLM, ClassificationMethod.UNCLASSIFIED]

    def test_empty_log(self):
        """Test handling of empty logs"""
        result = classify_log("System", "")
        assert result["category"] == "Unclassified"
