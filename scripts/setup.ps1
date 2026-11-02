# ==============================================================================
# DOCUMIND AI — LOCAL ENVIRONMENT SETUP SCRIPT (WINDOWS POWERSHELL)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   DocuMind AI — Free-First Setup & Prerequisite Check    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$AllGood = $true

# 1. Check Python
Write-Host "[1/5] Checking Python installation..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host " NOT FOUND!" -ForegroundColor Red
    Write-Host "Please install Python 3.11 from https://www.python.org/downloads/" -ForegroundColor Yellow
    $AllGood = $false
}

# 2. Check Node.js
Write-Host "[2/5] Checking Node.js runtime..." -NoNewline
try {
    $nodeVersion = node --version 2>&1
    Write-Host " Found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host " NOT FOUND!" -ForegroundColor Red
    Write-Host "Please install Node.js 20+ from https://nodejs.org/" -ForegroundColor Yellow
    $AllGood = $false
}

# 3. Check npm
Write-Host "[3/5] Checking npm package manager..." -NoNewline
try {
    $npmVersion = npm --version 2>&1
    Write-Host " Found: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host " NOT FOUND!" -ForegroundColor Red
    $AllGood = $false
}

# 4. Check Docker Desktop
Write-Host "[4/5] Checking Docker Desktop..." -NoNewline
try {
    $dockerVersion = docker --version 2>&1
    Write-Host " Found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host " WARNING (Optional for local mode, required for full stack container deployment)" -ForegroundColor Yellow
}

# 5. Check Docker Compose
Write-Host "[5/5] Checking Docker Compose..." -NoNewline
try {
    $composeVersion = docker compose version 2>&1
    Write-Host " Found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host " WARNING (Docker Compose not found)" -ForegroundColor Yellow
}

Write-Host ""
if (-not $AllGood) {
    Write-Host "Missing essential prerequisites. Please install required software and re-run setup.ps1." -ForegroundColor Red
    exit 1
}

# Setup Python Virtual Environment
Write-Host "Setting up Python virtual environment in backend/.venv..." -ForegroundColor Cyan
if (-not (Test-Path "backend\.venv")) {
    python -m venv backend\.venv
}

$VenvPython = "backend\.venv\Scripts\python.exe"
$VenvPip = "backend\.venv\Scripts\pip.exe"

# Install backend dependencies
Write-Host "Installing backend Python dependencies..." -ForegroundColor Cyan
& $VenvPip install -r backend\requirements.txt

# Install frontend dependencies
Write-Host "Installing Next.js frontend dependencies..." -ForegroundColor Cyan
Push-Location frontend
npm install
Pop-Location

# Generate Synthetic Invoices
Write-Host "Generating synthetic business invoices for zero-cost testing..." -ForegroundColor Cyan
$env:PYTHONPATH = "backend"
& $VenvPython scripts\generate_synthetic_invoices.py

# Seed Database
Write-Host "Initializing database & seeding demonstration records..." -ForegroundColor Cyan
& $VenvPython scripts\seed_db.py

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   Setup Completed Successfully!                         " -ForegroundColor Green
Write-Host "   To start the platform: .\start.ps1                     " -ForegroundColor Green
Write-Host "   To execute test suite: .\test.ps1                      " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

