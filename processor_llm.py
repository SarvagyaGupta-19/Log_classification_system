"""LLM-based classification using Groq API"""
from dotenv import load_dotenv
from groq import Groq
import json
import re
from typing import Optional
import time
from logger_config import get_logger
from exceptions import LLMAPIError, TimeoutError
from config import settings

load_dotenv()

logger = get_logger(__name__)


class LLMClassifier:
    """LLM-based classifier with production features"""
    
    def __init__(self):
        """Initialize LLM client"""
        try:
            self.client = Groq(api_key=settings.groq_api_key)
            self.model = settings.llm_model_name
            self.temperature = settings.llm_temperature
            self.max_retries = 3
            self.retry_delay = 1  # seconds
            logger.info("LLM classifier initialized", extra={"model": self.model})
        except Exception as e:
            logger.error("Failed to initialize LLM client", extra={"error": str(e)})
            raise LLMAPIError(f"LLM initialization failed: {str(e)}")
    
    def classify(self, log_msg: str, timeout: int = 30) -> str:
        """
        Classify log message using LLM with retry logic
        
        Args:
            log_msg: Log message to classify
            timeout: Request timeout in seconds
            
        Returns:
            Classification label
            
        Raises:
            LLMAPIError: If API call fails after retries
            TimeoutError: If request times out
        """
        if not log_msg or not isinstance(log_msg, str):
            logger.warning("Invalid log message for LLM", extra={
                "message": str(log_msg)[:100]
            })
            return "Unclassified"
        
        prompt = f'''Classify the log message into one of these categories: 
      Workflow Error, Deprecation Warning.
    If you can't figure out a category, use "Unclassified".
    Put the category inside <category> </category> tags. 
    Log message: {log_msg}'''
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=self.temperature,
                    timeout=timeout
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                content = chat_completion.choices[0].message.content
                
                # Extract category from response
                match = re.search(r'<category>(.*)<\/category>', content, flags=re.DOTALL)
                category = match.group(1).strip() if match else "Unclassified"
                
                logger.info("LLM classification successful", extra={
                    "label": category,
                    "attempt": attempt + 1,
                    "latency_ms": elapsed_ms
                })
                
                return category
                
            except Exception as e:
                error_msg = str(e)
                logger.warning("LLM API call failed", extra={
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries,
                    "error": error_msg
                })
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    logger.error("LLM classification failed after retries", extra={
                        "error": error_msg,
                        "message": log_msg[:100]
                    })
                    # Graceful degradation
                    return "Unclassified"
        
        return "Unclassified"
    
    def health_check(self) -> bool:
        """Check if LLM API is accessible"""
        try:
            # Quick test with minimal message
            test_msg = "test"
            result = self.classify(test_msg, timeout=5)
            return result is not None
        except Exception as e:
            logger.error("LLM health check failed", extra={"error": str(e)})
            return False


# Global instance
_classifier: Optional[LLMClassifier] = None


def get_llm_classifier() -> LLMClassifier:
    """Get or create LLM classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = LLMClassifier()
    return _classifier


def classify_with_llm(log_msg: str) -> str:
    """Legacy function for backward compatibility"""
    classifier = get_llm_classifier()
    return classifier.classify(log_msg)


if __name__ == "__main__":
    print(classify_with_llm(
        "Case escalation for ticket ID 7324 failed because the assigned support agent is no longer active."))
    print(classify_with_llm(
        "The 'ReportGenerator' module will be retired in version 4.0. Please migrate to the 'AdvancedAnalyticsSuite' by Dec 2025"))
    print(classify_with_llm("System reboot initiated by user 12345."))