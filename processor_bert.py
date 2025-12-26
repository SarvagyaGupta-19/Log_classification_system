"""
BERT-based log classification with embeddings

This module uses sentence-transformers for semantic understanding of log messages.

Model Details:
- Embedding Model: all-MiniLM-L6-v2 (80MB, fast inference)
- Classification: LogisticRegression trained on 10K+ logs
- Confidence Threshold: 0.5 (adjustable via config)
- Average Latency: 50-100ms per log

The BERT classifier provides a balance between accuracy and speed,
handling logs that don't match simple regex patterns.
"""
import joblib
from sentence_transformers import SentenceTransformer
from typing import Optional, Tuple
import numpy as np
from functools import lru_cache
from logger_config import get_logger
from exceptions import ModelLoadError, ClassificationError
from config import settings
import os

logger = get_logger(__name__)


class BERTClassifier:
    """BERT-based log classifier with production features"""
    
    def __init__(self):
        """Initialize BERT models with error handling"""
        self.model_embedding: Optional[SentenceTransformer] = None
        self.model_classification: Optional[any] = None
        self.confidence_threshold = settings.bert_confidence_threshold
        self._load_models()
    
    def _load_models(self):
        """Load BERT models with error handling"""
        try:
            logger.info("Loading BERT embedding model", extra={
                "model": settings.bert_model_name
            })
            self.model_embedding = SentenceTransformer(settings.bert_model_name)
            
            classifier_path = settings.classifier_model_path
            if not os.path.exists(classifier_path):
                raise ModelLoadError(f"Classifier model not found: {classifier_path}")
            
            logger.info("Loading classification model", extra={
                "path": classifier_path
            })
            self.model_classification = joblib.load(classifier_path)
            
            logger.info("BERT models loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load BERT models", extra={"error": str(e)})
            raise ModelLoadError(f"BERT model loading failed: {str(e)}")
    
    def classify(self, log_message: str) -> Tuple[str, float]:
        """
        Classify log message using BERT embeddings
        
        Args:
            log_message: Log message to classify
            
        Returns:
            Tuple of (label, confidence)
            
        Raises:
            ClassificationError: If classification fails
        """
        if not log_message or not isinstance(log_message, str):
            logger.warning("Invalid log message for BERT", extra={
                "message": str(log_message)[:100]
            })
            return "Unclassified", 0.0
        
        if not self.model_embedding or not self.model_classification:
            raise ClassificationError("BERT models not loaded")
        
        try:
            # Generate embeddings
            embeddings = self.model_embedding.encode([log_message])
            
            # Get predictions
            probabilities = self.model_classification.predict_proba(embeddings)[0]
            max_prob = float(np.max(probabilities))
            
            # Check confidence threshold
            if max_prob < self.confidence_threshold:
                logger.debug("Low confidence prediction", extra={
                    "confidence": max_prob,
                    "threshold": self.confidence_threshold
                })
                return "Unclassified", max_prob
            
            predicted_label = self.model_classification.predict(embeddings)[0]
            
            logger.debug("BERT classification successful", extra={
                "label": predicted_label,
                "confidence": max_prob
            })
            
            return predicted_label, max_prob
            
        except Exception as e:
            logger.error("BERT classification failed", extra={
                "error": str(e),
                "message": log_message[:100]
            })
            raise ClassificationError(f"BERT classification failed: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if models are loaded and functional"""
        try:
            if not self.model_embedding or not self.model_classification:
                return False
            # Test with sample message
            test_message = "System test message"
            self.model_embedding.encode([test_message])
            return True
        except Exception as e:
            logger.error("BERT health check failed", extra={"error": str(e)})
            return False


# Global instance
_classifier: Optional[BERTClassifier] = None


def get_bert_classifier() -> BERTClassifier:
    """Get or create BERT classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = BERTClassifier()
    return _classifier


def classify_with_bert(log_message: str) -> str:
    """Legacy function for backward compatibility"""
    classifier = get_bert_classifier()
    label, confidence = classifier.classify(log_message)
    return label


if __name__ == "__main__":
    logs = [
        "alpha.osapi_compute.wsgi.server - 12.10.11.1 - API returned 404 not found error",
        "GET /v2/3454/servers/detail HTTP/1.1 RCODE   404 len: 1583 time: 0.1878400",
        "System crashed due to drivers errors when restarting the server",
        "Hey bro, chill ya!",
        "Multiple login failures occurred on user 6454 account",
        "Server A790 was restarted unexpectedly during the process of data transfer"
    ]
    for log in logs:
        label = classify_with_bert(log)
        print(log, "->", label)
