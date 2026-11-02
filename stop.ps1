# ==============================================================================
# DOCUMIND AI — STOP SERVICES SCRIPT (WINDOWS POWERSHELL)
# ==============================================================================

Write-Host "Stopping DocuMind AI services..." -ForegroundColor Cyan

# Stop Docker Compose if running
try {
    docker compose down 2>$null
} catch {}

# Stop background local processes if PIDs file exists
if (Test-Path ".documind_pids.json") {
    try {
        $pids = Get-Content ".documind_pids.json" | ConvertFrom-Json
        if ($pids.BackendId) {
            Stop-Process -Id $pids.BackendId -Force -ErrorAction SilentlyContinue
        }
        if ($pids.FrontendId) {
            Stop-Process -Id $pids.FrontendId -Force -ErrorAction SilentlyContinue
        }
        Remove-Item ".documind_pids.json" -Force -ErrorAction SilentlyContinue
    } catch {}
}

# Cleanup lingering node or uvicorn processes on standard ports
Get-Process | Where-Object { $_.ProcessName -match "uvicorn|node" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "All DocuMind AI services stopped successfully." -ForegroundColor Green

