#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Production Startup Script for Log Classification System
    Owner: DevOps Engineer
    
.DESCRIPTION
    Comprehensive startup script with health checks and validation
    
.PARAMETER Port
    Port to run the server on (default: 8000)
    
.PARAMETER Workers
    Number of worker processes (default: 1)
    
.PARAMETER Mode
    Run mode: dev or production (default: dev)
#>

param(
    [int]$Port = 8000,
    [int]$Workers = 1,
    [string]$Mode = "dev"
)

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Green "=================================================="
Write-ColorOutput Green "  Log Classification System - Production Startup"
Write-ColorOutput Green "=================================================="
Write-Output ""

# Check Python version
Write-Output "[1/8] Checking Python version..."
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "ERROR: Python not found. Please install Python 3.8+"
    exit 1
}
Write-ColorOutput Green "✓ $pythonVersion"
Write-Output ""

# Check if virtual environment exists
Write-Output "[2/8] Checking virtual environment..."
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-ColorOutput Green "✓ Virtual environment found"
    & "venv\Scripts\Activate.ps1"
} else {
    Write-ColorOutput Yellow "⚠ Virtual environment not found. Creating one..."
    python -m venv venv
    & "venv\Scripts\Activate.ps1"
    Write-ColorOutput Green "✓ Virtual environment created"
}
Write-Output ""

# Check and install dependencies
Write-Output "[3/8] Checking dependencies..."
$requirementsHash = (Get-FileHash -Path "requirements.txt" -Algorithm MD5).Hash
$installedHash = ""
if (Test-Path ".requirements.hash") {
    $installedHash = Get-Content ".requirements.hash"
}

if ($requirementsHash -ne $installedHash) {
    Write-ColorOutput Yellow "⚠ Dependencies need to be updated"
    Write-Output "Installing dependencies (this may take a few minutes)..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        $requirementsHash | Out-File -FilePath ".requirements.hash"
        Write-ColorOutput Green "✓ Dependencies installed successfully"
    } else {
        Write-ColorOutput Red "ERROR: Failed to install dependencies"
        exit 1
    }
} else {
    Write-ColorOutput Green "✓ Dependencies up to date"
}
Write-Output ""

# Check required directories
Write-Output "[4/8] Checking directories..."
$requiredDirs = @("resources", "models", "logs")
foreach ($dir in $requiredDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-ColorOutput Yellow "⚠ Created missing directory: $dir"
    }
}
Write-ColorOutput Green "✓ All required directories exist"
Write-Output ""

# Check .env file
Write-Output "[5/8] Checking configuration..."
if (!(Test-Path ".env")) {
    Write-ColorOutput Yellow "⚠ .env file not found. Creating from template..."
    @"
# Application Configuration
APP_NAME=Log Classification System
ENVIRONMENT=$Mode
DEBUG=False
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=$Port
WORKERS=$Workers

# ML Model Configuration
BERT_MODEL_NAME=all-MiniLM-L6-v2
BERT_CONFIDENCE_THRESHOLD=0.5

# LLM API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Processing Configuration
CLASSIFICATION_TIMEOUT=30
MAX_FILE_SIZE_MB=50
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-ColorOutput Yellow "⚠ Please edit .env file and add your API keys"
}
Write-ColorOutput Green "✓ Configuration file exists"
Write-Output ""

# Check model files
Write-Output "[6/8] Checking ML models..."
if (!(Test-Path "models\log_classifier.joblib")) {
    Write-ColorOutput Red "ERROR: Model file not found: models\log_classifier.joblib"
    Write-Output "Please train the model first or copy it from Model_training directory"
    exit 1
}
Write-ColorOutput Green "✓ Model files found"
Write-Output ""

# Run tests (optional in dev mode)
if ($Mode -eq "dev") {
    Write-Output "[7/8] Running tests..."
    if (Test-Path "tests") {
        python -m pytest tests -v --tb=short 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✓ All tests passed"
        } else {
            Write-ColorOutput Yellow "⚠ Some tests failed (continuing anyway in dev mode)"
        }
    } else {
        Write-ColorOutput Yellow "⚠ No tests directory found"
    }
} else {
    Write-Output "[7/8] Skipping tests in production mode"
    Write-ColorOutput Green "✓ Skipped"
}
Write-Output ""

# Start server
Write-Output "[8/8] Starting server..."
Write-Output ""
Write-ColorOutput Green "=================================================="
Write-ColorOutput Green "  Server Configuration"
Write-ColorOutput Green "=================================================="
Write-Output "Mode:          $Mode"
Write-Output "Port:          $Port"
Write-Output "Workers:       $Workers"
Write-Output "URL:           http://localhost:$Port"
Write-Output "Docs:          http://localhost:$Port/docs"
Write-Output "Health:        http://localhost:$Port/health"
Write-Output "Metrics:       http://localhost:$Port/metrics"
Write-Output ""
Write-ColorOutput Green "=================================================="
Write-ColorOutput Yellow "Press Ctrl+C to stop the server"
Write-ColorOutput Green "=================================================="
Write-Output ""

if ($Mode -eq "dev") {
    # Development mode with auto-reload
    uvicorn server:app --host 0.0.0.0 --port $Port --reload --log-level info
} else {
    # Production mode
    uvicorn server:app --host 0.0.0.0 --port $Port --workers $Workers --log-level warning
}
