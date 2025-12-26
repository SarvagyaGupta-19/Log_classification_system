"""Custom exception hierarchy"""


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
