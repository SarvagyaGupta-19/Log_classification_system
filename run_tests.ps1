#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test Runner Script
    Owner: QA Engineer
#>

Write-Host "=================================================="  -ForegroundColor Cyan
Write-Host "  Running Test Suite"  -ForegroundColor Cyan
Write-Host "=================================================="  -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "ERROR: Virtual environment not found. Run setup.ps1 first" -ForegroundColor Red
    exit 1
}

# Install test dependencies
Write-Host "Installing test dependencies..."
pip install -q pytest pytest-asyncio httpx

# Run tests
Write-Host ""
Write-Host "Running unit tests..." -ForegroundColor Cyan
python -m pytest tests -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Some tests failed" -ForegroundColor Red
    exit 1
}
