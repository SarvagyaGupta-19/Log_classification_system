"""
FastAPI server for log classification with visualization

This module provides a REST API for log classification with:
- Single and batch log classification
- Multiple visualization types (bar charts, pie charts, dashboards)
- Severity analysis and insights
- CSV file processing with result download
- Interactive API documentation via Swagger UI
- Health monitoring and metrics tracking
- Professional Web UI Dashboard
"""
import pandas as pd
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import time

from classify import classify
from config import settings
from logger_config import get_logger, setup_logging
from metrics import get_metrics
from models import ClassificationResponse, HealthStatus, ErrorResponse, MetricsResponse
from exceptions import FileProcessingError, ClassificationError
from processor_bert import get_bert_classifier
from visualization import LogVisualizer, create_insights_report
from severity_mapper import get_severity, get_severity_icon, get_severity_stats
from csv_mapper import smart_csv_mapping, format_mapping_summary
from log_converter import parse_plain_text, parse_timestamped_logs, parse_syslog, parse_json_logs, parse_apache_logs
import io

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
    
    # Server starts immediately - models load on first use
    logger.info("Server ready - models will load on first classification request")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application", extra={
        "total_requests": metrics.request_count,
        "uptime_seconds": metrics.get_uptime_seconds()
    })


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Log classification system with multi-stage ML pipeline, severity analysis, and interactive visualizations",
    lifespan=lifespan
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
            "classification_engine": "healthy" if bert_healthy else "unhealthy",
            "secondary_classifier": "healthy" if llm_healthy else "degraded",
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
    try:
        # Use lock to safely read all metrics at once
        with metrics._lock:
            total_class = metrics.total_classifications
            methods = metrics.classifications_by_method.copy()
            avg_time = metrics.get_average_processing_time()
            err_rate = metrics.get_error_rate()
        
        # Get uptime without lock (time.time() is thread-safe)
        uptime = metrics.get_uptime_seconds()
        
        return MetricsResponse(
            total_classifications=total_class,
            classifications_by_method=methods,
            average_processing_time_ms=avg_time,
            error_rate=err_rate,
            uptime_seconds=uptime
        )
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        # Return empty metrics instead of failing
        return MetricsResponse(
            total_classifications=0,
            classifications_by_method={"regex": 0, "bert": 0, "llm": 0},
            average_processing_time_ms=0.0,
            error_rate=0.0,
            uptime_seconds=0.0
        )


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint - redirects to dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)


# ─────────────────────────────────────────────
# Classification Endpoints
# ─────────────────────────────────────────────

@app.post("/classify/", response_model=ClassificationResponse, tags=["Classification"])
async def classify_logs(file: UploadFile, request: Request):
    """
    Classify logs from uploaded CSV file
    
    - **file**: CSV file or raw log file (.csv, .log, .txt, .json, .jsonl)
    - Returns: JSON response with classification summary and file path
    
    Supported formats:
    - CSV: Directly processed (columns auto-detected)
    - Plain text (.log, .txt): One log per line
    - JSON (.json, .jsonl): One JSON object per line
    - Auto-detection for timestamped and syslog formats
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Validate file type - accept CSV and raw log files
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded"
        )
    
    allowed_extensions = ['.csv', '.log', '.txt', '.json', '.jsonl']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
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
        df = None
        encoding_used = None
        conversion_info = None
        
        # Determine if conversion is needed
        if file_ext == '.csv':
            # CSV file - read directly with encoding fallback
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
            
            for encoding in encodings:
                try:
                    await file.seek(0)
                    df = pd.read_csv(file.file, encoding=encoding, on_bad_lines='skip')
                    encoding_used = encoding
                    break
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
            
            if df is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to read CSV file. Please ensure it's properly formatted and uses standard encoding (UTF-8, Latin-1, etc.)"
                )
            
            # Log encoding if non-standard
            if encoding_used != 'utf-8':
                logger.warning(f"CSV read with {encoding_used} encoding", extra={
                    "request_id": request_id,
                    "encoding": encoding_used
                })
        
        else:
            # Raw log file - convert to CSV format
            logger.info(f"Converting {file_ext} file to CSV", extra={
                "request_id": request_id,
                "filename": file.filename
            })
            
            # Read file content
            await file.seek(0)
            content = content.decode('utf-8', errors='ignore')
            
            # Save to temporary file for parsing
            temp_file_path = os.path.join(settings.resources_dir, f"temp_{request_id}{file_ext}")
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Detect format and convert
            logs = []
            source_name = os.path.splitext(file.filename)[0]
            
            try:
                # Try JSON format first
                if file_ext in ['.json', '.jsonl']:
                    logs = parse_json_logs(temp_file_path)
                    conversion_info = f"JSON format detected and converted"
                else:
                    # Auto-detect between plain, timestamped, and syslog
                    # Try syslog pattern first
                    syslog_logs = parse_syslog(temp_file_path, source_name)
                    if len(syslog_logs) > 0:
                        logs = syslog_logs
                        conversion_info = f"Syslog format detected and converted"
                    else:
                        # Try timestamped
                        timestamped_logs = parse_timestamped_logs(temp_file_path, source_name)
                        if len(timestamped_logs) > 0:
                            logs = timestamped_logs
                            conversion_info = f"Timestamped format detected and converted"
                        else:
                            # Fallback to plain text
                            logs = parse_plain_text(temp_file_path, source_name)
                            conversion_info = f"Plain text format processed"
                
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
                if not logs:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No valid log entries found in file"
                    )
                
                # Convert logs to DataFrame
                df = pd.DataFrame(logs)
                encoding_used = 'utf-8'
                
                logger.info(f"Converted {len(logs)} logs from {file_ext}", extra={
                    "request_id": request_id,
                    "log_count": len(logs),
                    "format": conversion_info
                })
            
            except Exception as e:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to parse log file: {str(e)}"
                )
        
        # Check if CSV is empty
        if df.empty or len(df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file contains no data rows"
            )
        
        # Check if CSV has no columns
        if len(df.columns) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file has no columns. Please ensure proper formatting."
            )
        
        # Smart column mapping - automatically detect and map columns
        df, mapping_info = smart_csv_mapping(df)
        
        # After mapping, check if we have valid data
        if df.empty or len(df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid log entries found after processing. All rows were empty or invalid."
            )
        
        # Log mapping information
        mapping_summary = format_mapping_summary(mapping_info)
        logger.info("CSV columns mapped", extra={
            "request_id": request_id,
            "original_columns": mapping_info['original_columns'],
            "auto_assigned": mapping_info['auto_assigned'],
            "warnings": mapping_info['warnings'],
            "encoding": encoding_used,
            "conversion": conversion_info
        })
        
        # Validate log messages are not empty
        empty_messages = df['log_message'].isna().sum() + (df['log_message'].str.strip() == '').sum()
        if empty_messages > 0:
            logger.warning(f"Found {empty_messages} empty log messages", extra={
                "request_id": request_id,
                "empty_count": empty_messages
            })
            # Remove rows with empty messages
            df = df[df['log_message'].notna() & (df['log_message'].str.strip() != '')]
            
            if df.empty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All log messages are empty. CSV must contain valid text data."
                )
        
        total_logs = len(df)
        logger.info("Processing classification request", extra={
            "request_id": request_id,
            "filename": file.filename,
            "rows": total_logs,
            "size_mb": file_size_mb
        })
        
        # Perform classification
        classification_results = classify(list(zip(df["source"], df["log_message"])))
        
        # Add results to DataFrame
        df["target_label"] = [r["category"] for r in classification_results]
        df["method"] = [r["method"] for r in classification_results]
        df["confidence"] = [r["confidence"] for r in classification_results]
        
        # Add severity information
        df["severity"] = df["target_label"].apply(lambda x: get_severity(x).value)
        df["severity_icon"] = df["target_label"].apply(lambda x: get_severity_icon(get_severity(x)))
        
        # Save results
        os.makedirs(settings.resources_dir, exist_ok=True)
        output_file = settings.output_file
        df.to_csv(output_file, index=False)
        
        # Get severity stats
        full_severity_stats = get_severity_stats(df["target_label"].tolist())
        
        # Get category distribution
        category_stats = df["target_label"].value_counts().to_dict()
        
        # Format severity stats for frontend (flatten the structure)
        severity_counts = full_severity_stats.get("severity_counts", {})
        
        logger.info("Classification complete", extra={
            "request_id": request_id,
            "total_logs": total_logs,
            "output_file": output_file,
            "critical_count": full_severity_stats.get("critical_count", 0)
        })
        
        return JSONResponse(content={
            "status": "success",
            "total_logs": total_logs,
            "output_file": output_file,
            "severity_stats": severity_counts,  # Flattened for easier frontend access
            "full_severity_stats": full_severity_stats,  # Complete stats
            "category_stats": category_stats,
            "download_url": "/download/",
            "visualizations_url": "/visualize/",
            "dashboard_url": "/dashboard",
            "insights_url": "/insights/",
            "column_mapping": {
                "original_columns": mapping_info['original_columns'],
                "message_from": mapping_info['message_source'],
                "source_from": mapping_info['source_source'],
                "warnings": mapping_info['warnings'],
                "converted_from": conversion_info or "CSV (no conversion needed)"
            }
        })
    
    except HTTPException:
        raise
    except pd.errors.EmptyDataError:
        logger.error("Empty CSV file", extra={"request_id": request_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or contains no data"
        )
    except pd.errors.ParserError as e:
        logger.error("CSV parsing failed", extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed CSV file. Please check formatting: {str(e)}"
        )
    except UnicodeDecodeError as e:
        logger.error("Encoding error", extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please save your CSV with UTF-8 encoding."
        )
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


@app.get("/download/", tags=["Results"])
async def download_results(request: Request):
    """
    Download classified results as CSV
    
    - Requires: Previous classification results in output.csv
    - Returns: CSV file with classified logs
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        output_file = settings.output_file
        
        if not os.path.exists(output_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No classification results found. Please classify a file first."
            )
        
        logger.info("Serving classification results", extra={
            "request_id": request_id,
            "output_file": output_file
        })
        
        return FileResponse(
            output_file,
            media_type='text/csv',
            filename=f"classified_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            headers={"X-Request-ID": request_id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Download failed", extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


# ─────────────────────────────────────────────
# Visualization Endpoints
# ─────────────────────────────────────────────

@app.get("/visualize/", tags=["Visualization"])
async def get_visualizations(request: Request):
    """
    Get all visualizations as JSON with base64 encoded images
    
    - Requires: Previous classification results in output.csv
    - Returns: JSON with charts, stats, and insights
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        output_file = settings.output_file
        
        if not os.path.exists(output_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No classification results found. Please classify a file first."
            )
        
        # Read results
        df = pd.read_csv(output_file)
        
        # Validate required columns
        required_cols = ["target_label", "method", "confidence"]
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Results file missing required columns: {required_cols}"
            )
        
        # Generate visualizations
        visualizer = LogVisualizer(df)
        visualizations = visualizer.generate_all_visualizations()
        
        logger.info("Visualizations generated", extra={
            "request_id": request_id,
            "total_logs": len(df)
        })
        
        return JSONResponse(content=visualizations)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Visualization generation failed", extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visualization failed: {str(e)}"
        )


@app.get("/insights/", tags=["Visualization"])
async def get_insights(request: Request):
    """
    Get text-based insights report
    
    - Requires: Previous classification results in output.csv
    - Returns: Plain text insights report
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        output_file = settings.output_file
        
        if not os.path.exists(output_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No classification results found. Please classify a file first."
            )
        
        # Read results
        df = pd.read_csv(output_file)
        
        # Generate insights report
        report = create_insights_report(df)
        
        logger.info("Insights report generated", extra={
            "request_id": request_id
        })
        
        return JSONResponse(content={"report": report})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Insights generation failed", extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insights generation failed: {str(e)}"
        )


@app.get("/dashboard", response_class=HTMLResponse, tags=["Visualization"])
async def dashboard(request: Request):
    """
    Interactive web dashboard with visualizations
    
    - Simple frontend dashboard
    - Upload and classify logs through UI
    - View results and analytics
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        # Simple dashboard - just return the template
        logger.info("Dashboard accessed", extra={"request_id": request_id})
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request
            }
        )
    
    except Exception as e:
        logger.error("Dashboard error", extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
