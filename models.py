"""Pydantic models for request/response validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class LogSource(str, Enum):
    """Valid log sources"""
    LEGACY_CRM = "LegacyCRM"
    WEB_SERVER = "WebServer"
    DATABASE = "Database"
    API_GATEWAY = "APIGateway"
    OTHER = "Other"


class ClassificationMethod(str, Enum):
    """Classification methods"""
    REGEX = "regex"
    BERT = "bert"
    LLM = "llm"
    UNCLASSIFIED = "unclassified"


class LogEntry(BaseModel):
    """Single log entry"""
    source: str = Field(..., min_length=1, max_length=100)
    log_message: str = Field(..., min_length=1, max_length=5000)
    
    @validator('log_message')
    def validate_message(cls, v):
        """Validate log message is not empty or whitespace"""
        if not v or not v.strip():
            raise ValueError("Log message cannot be empty")
        return v.strip()


class ClassificationResult(BaseModel):
    """Classification result for a single log"""
    source: str
    log_message: str
    target_label: str
    classification_method: ClassificationMethod
    confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None


class ClassificationResponse(BaseModel):
    """Response from classification endpoint"""
    job_id: Optional[str] = None
    status: str
    total_logs: int
    processed: int
    results: Optional[List[ClassificationResult]] = None
    download_url: Optional[str] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class MetricsResponse(BaseModel):
    """Metrics endpoint response"""
    total_classifications: int
    classifications_by_method: dict
    average_processing_time_ms: float
    error_rate: float
    uptime_seconds: float
