"""
Custom exception hierarchy for structured error handling

Enables fine-grained exception catching and proper HTTP status mapping.

Exception Types:
- LogClassifierException: Base class for all system errors
- ModelLoadError: ML model initialization failures (BERT/classifier)
- ClassificationError: Runtime classification errors
- ValidationError: Input validation failures

Error Handling Strategy:
- Specific exceptions for different failure modes
- Enables targeted error recovery (e.g., fallback to next processor)
- FastAPI exception handlers map to appropriate HTTP status codes

Usage Example:
    try:
        result = bert_processor.classify(log)
    except ModelLoadError:
        # Fall back to LLM processor
        result = llm_processor.classify(log)
"""


class LogClassifierException(Exception):
    """Base exception for log classifier"""
    pass


class ModelLoadError(LogClassifierException):
    """Raised when ML model fails to load"""
    pass


class ClassificationError(LogClassifierException):
    """Raised when classification fails"""
    pass


class ValidationError(LogClassifierException):
    """Raised when input validation fails"""
    pass


class TimeoutError(LogClassifierException):
    """Raised when operation times out"""
    pass


class FileProcessingError(LogClassifierException):
    """Raised when file processing fails"""
    pass


class LLMAPIError(LogClassifierException):
    """Raised when LLM API call fails"""
    pass
