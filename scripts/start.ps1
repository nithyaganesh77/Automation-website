# ==============================================================================
# DOCUMIND AI — STARTUP SCRIPT (WINDOWS POWERSHELL)
# ==============================================================================

param (
    [switch]$Docker
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "             Starting DocuMind AI SaaS Platform           " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

if ($Docker) {
    Write-Host "Launching multi-container Docker Compose stack (Free Local Infrastructure)..." -ForegroundColor Yellow
    docker compose up -d
    Write-Host ""
    Write-Host "Containers started! Access services:" -ForegroundColor Green
    Write-Host " - Frontend Dashboard: http://localhost:3000" -ForegroundColor White
    Write-Host " - Backend API Docs:   http://localhost:8000/docs" -ForegroundColor White
    Write-Host " - Prometheus Metrics: http://localhost:9090" -ForegroundColor White
    Write-Host " - Grafana Dashboards: http://localhost:3001 (admin/admin)" -ForegroundColor White
    Write-Host " - MinIO S3 Console:   http://localhost:9001 (minioadmin/minioadmin)" -ForegroundColor White
    Write-Host " - Qdrant Vector DB:   http://localhost:6333/dashboard" -ForegroundColor White
    exit 0
}

# Local Mode
$env:PYTHONPATH = "backend"
$VenvUvicorn = "backend\.venv\Scripts\uvicorn.exe"

Write-Host "Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Cyan
$BackendJob = Start-Process -FilePath $VenvUvicorn -ArgumentList "app.main:app --port 8000 --reload" -PassThru -WindowStyle Minimized

Write-Host "Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Cyan
Push-Location frontend
$FrontendJob = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -PassThru -WindowStyle Minimized
Pop-Location

# Save process IDs for clean stop
$Pids = @{
    BackendId = $BackendJob.Id
    FrontendId = $FrontendJob.Id
}
$Pids | ConvertTo-Json | Out-File -FilePath ".documind_pids.json" -Encoding utf8

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   DocuMind AI is Running Locally!                        " -ForegroundColor Green
Write-Host "   - Frontend UI: http://localhost:3000                   " -ForegroundColor White
Write-Host "   - Backend API Docs: http://localhost:8000/docs         " -ForegroundColor White
Write-Host "   - Demo User: admin@documind.ai / Password123!          " -ForegroundColor Yellow
Write-Host "   To stop services gracefully: .\stop.ps1                " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green

