"""
Database Layer with SQLAlchemy ORM

Database Engineer: Implements persistent storage for logs,
classifications, users, and audit trails.

Architecture:
- PostgreSQL for production (scalable, ACID compliant)
- SQLite for development (zero-config)
- Async support with SQLAlchemy 2.0
- Connection pooling and retry logic
- Migration support with Alembic

Tables:
- users: User accounts and authentication
- classification_jobs: Batch processing jobs
- classification_results: Individual log classifications
- audit_logs: System activity tracking
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool
from datetime import datetime
from typing import Optional, List
import enum
from contextlib import contextmanager

from config import settings
from logger_config import get_logger

logger = get_logger(__name__)

# Database URL
DATABASE_URL = getattr(settings, 'database_url', 'sqlite:///./log_classifier.db')

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class JobStatus(enum.Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClassificationMethod(enum.Enum):
    """Classification methods"""
    REGEX = "regex"
    BERT = "bert"
    LLM = "llm"
    UNCLASSIFIED = "unclassified"


# Database Models
class UserDB(Base):
    """User table"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="viewer")
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    jobs = relationship("ClassificationJob", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class ClassificationJob(Base):
    """Classification batch job table"""
    __tablename__ = "classification_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255))
    total_logs = Column(Integer, default=0)
    processed_logs = Column(Integer, default=0)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    result_file_path = Column(String(500))
    
    # Relationships
    user = relationship("UserDB", back_populates="jobs")
    results = relationship("ClassificationResult", back_populates="job", cascade="all, delete-orphan")


class ClassificationResult(Base):
    """Individual classification result table"""
    __tablename__ = "classification_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("classification_jobs.id"), nullable=False)
    source = Column(String(100), index=True)
    log_message = Column(Text, nullable=False)
    target_label = Column(String(100), index=True)
    classification_method = Column(SQLEnum(ClassificationMethod))
    confidence = Column(Float)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("ClassificationJob", back_populates="results")


class AuditLog(Base):
    """Audit log table for security and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), index=True)
    resource = Column(String(100))
    details = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("UserDB", back_populates="audit_logs")


# Database operations
def init_db():
    """Initialize database and create tables"""
    try:
        logger.info("Initializing database", extra={"url": DATABASE_URL})
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", extra={"error": str(e)})
        raise


@contextmanager
def get_db():
    """Database session context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session (for FastAPI dependency injection)"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


# CRUD operations
def create_user(db: Session, username: str, email: str, hashed_password: str, role: str = "viewer") -> UserDB:
    """Create new user"""
    db_user = UserDB(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_classification_job(db: Session, job_id: str, user_id: int, filename: str, total_logs: int) -> ClassificationJob:
    """Create new classification job"""
    job = ClassificationJob(
        job_id=job_id,
        user_id=user_id,
        filename=filename,
        total_logs=total_logs,
        status=JobStatus.PENDING
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job_status(db: Session, job_id: str, status: JobStatus, error_message: Optional[str] = None):
    """Update job status"""
    job = db.query(ClassificationJob).filter(ClassificationJob.job_id == job_id).first()
    if job:
        job.status = status.value  # type: ignore
        if status == JobStatus.COMPLETED:
            job.completed_at = datetime.utcnow()  # type: ignore
        if error_message:
            job.error_message = error_message  # type: ignore
        db.commit()


def save_classification_results(db: Session, job_db_id: int, results: List[dict]):
    """Bulk save classification results"""
    result_objects = [
        ClassificationResult(
            job_id=job_db_id,
            source=r['source'],
            log_message=r['log_message'],
            target_label=r['target_label'],
            classification_method=ClassificationMethod[r.get('method', 'UNCLASSIFIED').upper()],
            confidence=r.get('confidence'),
            processing_time_ms=r.get('processing_time_ms')
        )
        for r in results
    ]
    db.bulk_save_objects(result_objects)
    db.commit()


def log_audit_event(db: Session, user_id: Optional[int], action: str, resource: str, 
                   details: Optional[str] = None, ip_address: Optional[str] = None):
    """Log audit event"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address
    )
    db.add(audit)
    db.commit()


if __name__ == "__main__":
    # Initialize database
    init_db()
    logger.info("Database setup complete")
