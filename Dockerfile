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
# Install Python dependencies
# Use CPU-only PyTorch to save space (Standard PyTorch is ~800MB, CPU-only is ~100MB)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu && \
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

# Expose port (Render sets $PORT env var, defaulting to 10000)
EXPOSE 10000

# Health check (timeout increased)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://0.0.0.0:${PORT:-10000}/health || exit 1

# Run with Gunicorn
# Use the PORT environment variable (Render requirement)
CMD gunicorn server:app \
     --workers 1 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:${PORT:-10000} \
     --timeout 120 \
     --access-logfile - \
     --error-logfile -
