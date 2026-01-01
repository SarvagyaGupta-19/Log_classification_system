""""
Centralized configuration management with environment variable support

12-factor app principles: All config through environment variables.

Configuration Categories:
- Application: Debug mode, logging level
- Server: Host, port, CORS origins
- ML Models: BERT model name, confidence thresholds
- API Keys: Groq API key for LLM (required)
- File Paths: Model persistence locations

Environment Loading:
- Reads from .env file (development)
- Falls back to environment variables (production)
- Provides sensible defaults where applicable

Caching: @lru_cache ensures singleton behavior
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Log Classification System"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Paths
    resources_dir: str = "resources"
    models_dir: str = "models"
    output_file: str = "resources/output.csv"
    plot_file: str = "resources/bar_plot.png"
    
    # ML Models
    bert_model_name: str = "all-MiniLM-L6-v2"
    classifier_model_path: str = "models/log_classifier.joblib"
    llm_model_name: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.5
    
    # Processing
    bert_confidence_threshold: float = 0.5
    classification_timeout: int = 30
    max_file_size_mb: int = 50
    
    # LLM API
    groq_api_key: str = ""
    
    # Security
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "sqlite:///./log_classifier.db"  # Change to PostgreSQL in production
    
    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Monitoring
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    # Job Queue
    use_async_processing: bool = False
    job_retention_hours: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
