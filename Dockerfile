# Production Dockerfile for Log Classification System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn[standard]

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /app/models /app/resources && \
    chown -R appuser:appuser /app/models /app/resources

# Switch to non-root user
USER appuser

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run with Gunicorn (1 worker for free tier)
CMD gunicorn server:app \
     --workers 1 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:7860 \
     --timeout 120 \
     --access-logfile - \
     --error-logfile -
