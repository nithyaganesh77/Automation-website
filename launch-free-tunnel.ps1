<#
.SYNOPSIS
    DocuMind AI — 100% Free Instant Public Launch Tunnel
    Generates a secure public HTTPS link (https://xxx.trycloudflare.com)
    accessible anywhere in the world at zero cost.
#>

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DocuMind AI - Free Live Public Cloud Launch Tunnel      " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Frontend and Backend are alive
try {
    $be = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "[OK] Backend API is live on port 8000" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Backend is not responding on port 8000. Running ./start.ps1..." -ForegroundColor Yellow
    & ".\start.ps1"
}

try {
    $fe = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3
    Write-Host "[OK] Frontend Web App is live on port 3000" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Frontend is not responding on port 3000. Please start frontend." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting Cloudflare Public HTTPS Tunnel for http://localhost:3000..." -ForegroundColor Cyan
Write-Host "Look for the public URL ending with .trycloudflare.com below:" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

& ".\scripts\cloudflared.exe" tunnel --url http://localhost:3000
