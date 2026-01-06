# Docker Deployment Script
# Builds and runs the application in a Docker container

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Host "ERROR: Docker is not installed!" -ForegroundColor Red
    Write-Host "Install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env from .env.example" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t log-classifier:1.0 .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting container..." -ForegroundColor Yellow

# Stop existing container if running
docker stop log-classifier 2>$null
docker rm log-classifier 2>$null

# Run container with .env file
docker run -d `
  --name log-classifier `
  -p 8000:8000 `
  --env-file .env `
  -v ${PWD}/models:/app/models `
  -v ${PWD}/resources:/app/resources `
  --restart unless-stopped `
  log-classifier:1.0

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS! Container is running" -ForegroundColor Green
    Write-Host "Dashboard: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Yellow
    Write-Host "  docker logs log-classifier -f     # View logs"
    Write-Host "  docker stop log-classifier        # Stop container"
    Write-Host "  docker start log-classifier       # Start container"
    Write-Host "  docker restart log-classifier     # Restart container"
} else {
    Write-Host "ERROR: Failed to start container!" -ForegroundColor Red
}
