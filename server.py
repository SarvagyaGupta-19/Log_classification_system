"""FastAPI server for log classification"""
import pandas as pd
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

# Optional matplotlib import for plotting
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from classify import classify
from config import settings
from logger_config import get_logger, setup_logging
from metrics import get_metrics
from models import ClassificationResponse, HealthStatus, ErrorResponse, MetricsResponse
from exceptions import FileProcessingError, ClassificationError
from processor_bert import get_bert_classifier
from processor_llm import get_llm_classifier

# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)
metrics = get_metrics()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application"""
    logger.info("Starting Log Classification System", extra={
        "version": settings.app_version,
        "environment": settings.environment
    })
    
    # Warm up models on startup
    try:
        logger.info("Warming up models...")
        bert_classifier = get_bert_classifier()
        logger.info("BERT model loaded successfully")
        
        # LLM is lazy-loaded when needed
        logger.info("Application startup complete")
    except Exception as e:
        logger.error("Failed to load models", extra={"error": str(e)})
    
    yield
    
    # Shutdown
    logger.info("Shutting down application", extra={
        "total_requests": metrics.request_count,
        "uptime_seconds": metrics.get_uptime_seconds()
    })


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade log classification system with multi-stage ML pipeline",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and add request ID"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    logger.info("Request started", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path
    })
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info("Request completed", extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        })
        
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Request failed", extra={
            "request_id": request_id,
            "error": str(e),
            "duration_ms": duration_ms
        })
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error("Unhandled exception", extra={
        "request_id": request_id,
        "error": str(exc),
        "type": type(exc).__name__
    })
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc) if settings.debug else "An unexpected error occurred",
            request_id=request_id
        ).model_dump()
    )


# ─────────────────────────────────────────────
# Health and Monitoring Endpoints
# ─────────────────────────────────────────────

@app.get("/health", response_model=HealthStatus, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint
    Returns service status and component health
    """
    try:
        bert_classifier = get_bert_classifier()
        bert_healthy = bert_classifier.health_check()
        
        # LLM check is optional since it requires API call
        llm_healthy = True  # Assume healthy, will fail gracefully if not
        
        services = {
            "bert_model": "healthy" if bert_healthy else "unhealthy",
            "llm_api": "healthy" if llm_healthy else "degraded",
            "file_system": "healthy" if os.path.exists(settings.resources_dir) else "unhealthy"
        }
        
        overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"
        
        return HealthStatus(
            status=overall_status,
            version=settings.app_version,
            services=services
        )
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)})
        return HealthStatus(
            status="unhealthy",
            version=settings.app_version,
            services={"error": str(e)}
        )


@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics_endpoint():
    """
    Get application metrics
    Returns classification statistics and performance metrics
    """
    metrics_data = metrics.to_dict()
    return MetricsResponse(
        total_classifications=metrics_data["total_classifications"],
        classifications_by_method=metrics_data["classifications_by_method"],
        average_processing_time_ms=metrics_data["average_processing_time_ms"],
        error_rate=metrics_data["error_rate"],
        uptime_seconds=metrics_data["uptime_seconds"]
    )


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


# ─────────────────────────────────────────────
# Classification Endpoints
# ─────────────────────────────────────────────

@app.post("/classify/", response_model=ClassificationResponse, tags=["Classification"])
async def classify_logs(file: UploadFile, request: Request):
    """
    Classify logs from uploaded CSV file
    
    - **file**: CSV file with 'source' and 'log_message' columns
    - Returns: Classified results as CSV download
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    # Check file size (prevent DoS)
    file_size_mb = 0
    try:
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )
        
        # Reset file pointer
        await file.seek(0)
        
    except Exception as e:
        logger.error("File size check failed", extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file"
        )
    
    try:
        # Read CSV
        df = pd.read_csv(file.file)
        
        # Validate required columns
        required_columns = ["source", "log_message"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV must contain columns: {', '.join(required_columns)}. Missing: {', '.join(missing_columns)}"
            )
        
        total_logs = len(df)
        logger.info("Processing classification request", extra={
            "request_id": request_id,
            "filename": file.filename,
            "rows": total_logs,
            "size_mb": file_size_mb
        })
        
        # Perform classification
        df["target_label"] = classify(list(zip(df["source"], df["log_message"])))
        
        # Save results
        os.makedirs(settings.resources_dir, exist_ok=True)
        output_file = settings.output_file
        df.to_csv(output_file, index=False)
        
        logger.info("Classification complete", extra={
            "request_id": request_id,
            "total_logs": total_logs,
            "output_file": output_file
        })
        
        return FileResponse(
            output_file,
            media_type='text/csv',
            filename=f"classified_{file.filename}",
            headers={"X-Request-ID": request_id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Classification failed", extra={
            "request_id": request_id,
            "error": str(e),
            "filename": file.filename
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )
    
    finally:
        await file.close()


# ─────────────────────────────────────────────
# Visualization Endpoints
# ─────────────────────────────────────────────

@app.get("/plot/", tags=["Visualization"])
async def generate_plot(request: Request):
    """
    Generate bar plot of log counts by source
    
    - Requires: Previous classification results in output.csv
    - Returns: PNG image of bar chart
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    if not MATPLOTLIB_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Matplotlib not installed. Install with: pip install matplotlib"
        )
    
    try:
        output_file = settings.output_file
        
        if not os.path.exists(output_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No classification results found. Please classify a file first."
            )
        
        df = pd.read_csv(output_file)
        
        if "source" not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'source' column not found in results"
            )
        
        # Count log messages by source
        source_counts = df['source'].value_counts()
        
        # Create bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(source_counts.index, source_counts.values, color='mediumseagreen')
        plt.xlabel("Source System", fontsize=12)
        plt.ylabel("Log Count", fontsize=12)
        plt.title("Log Messages per Source System", fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot
        os.makedirs(settings.resources_dir, exist_ok=True)
        plot_path = settings.plot_file
        plt.savefig(plot_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        logger.info("Plot generated successfully", extra={
            "request_id": request_id,
            "plot_path": plot_path
        })
        
        return FileResponse(
            plot_path,
            media_type="image/png",
            headers={"X-Request-ID": request_id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Plot generation failed", extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plot generation failed: {str(e)}"
        )
