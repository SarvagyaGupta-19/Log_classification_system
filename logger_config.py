"""Structured JSON logging configuration"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict, MutableMapping, Tuple
import json


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields (safely access custom attributes)
        if hasattr(record, "extra_fields") and isinstance(getattr(record, "extra_fields", None), dict):
            log_data.update(getattr(record, "extra_fields"))
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Create root logger
    logger = logging.getLogger("log_classifier")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context to log messages"""
    
    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> Tuple[str, MutableMapping[str, Any]]:
        """Add extra context to log messages"""
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = {"extra_fields": extra}
        return msg, kwargs


# Global logger instance
logger = setup_logging()


def get_logger(name: str, **context) -> LoggerAdapter:
    """
    Get a logger with additional context
    
    Args:
        name: Logger name (typically __name__)
        **context: Additional context to include in all log messages
    
    Returns:
        Logger adapter with context
    """
    base_logger = logging.getLogger("log_classifier")
    return LoggerAdapter(base_logger, context)
