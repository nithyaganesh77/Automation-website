# DocuMind AI — System & Service Health Status Script

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "           DocuMind AI System Health Status               " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Environment & Process Status
Write-Host "`n[1] Local Process Status:" -ForegroundColor Yellow

$backendConn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($backendConn) {
    Write-Host "  FastAPI Backend (Port 8000):   RUNNING (PID: $(($backendConn.OwningProcess -join ', ')))" -ForegroundColor Green
} else {
    Write-Host "  FastAPI Backend (Port 8000):   STOPPED" -ForegroundColor DarkGray
}

$frontendConn = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($frontendConn) {
    Write-Host "  Next.js Frontend (Port 3000):  RUNNING (PID: $(($frontendConn.OwningProcess -join ', ')))" -ForegroundColor Green
} else {
    Write-Host "  Next.js Frontend (Port 3000):  STOPPED" -ForegroundColor DarkGray
}

# 2. Docker Services Status
Write-Host "`n[2] Docker Container Status:" -ForegroundColor Yellow
try {
    $dockerPs = docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>&1
    if ($LASTEXITCODE -eq 0 -and $dockerPs) {
        Write-Host $dockerPs
    } else {
        Write-Host "  Docker Compose stack is not running." -ForegroundColor DarkGray
    }
} catch {
    Write-Host "  Docker daemon is not running." -ForegroundColor DarkGray
}

# 3. Database Connectivity
Write-Host "`n[3] Database Connectivity:" -ForegroundColor Yellow
if (Test-Path "documind.db") {
    $dbSize = (Get-Item "documind.db").Length / 1KB
    Write-Host "  SQLite Database (documind.db): READY ($([math]::Round($dbSize, 1)) KB)" -ForegroundColor Green
} else {
    Write-Host "  SQLite Database: NOT FOUND (Run setup.ps1 or seed_db.py)" -ForegroundColor Red
}

# 4. Live AI Provider Telemetry
Write-Host "`n[4] AI Provider Connectivity & Failover:" -ForegroundColor Yellow
if (Test-Path "backend\.venv\Scripts\python.exe") {
    & "backend\.venv\Scripts\python.exe" scripts\test_providers.py
} else {
    Write-Host "  Python virtual environment not found at backend\.venv" -ForegroundColor Red
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "                      Status Check Done                   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

