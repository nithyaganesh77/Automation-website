# ==============================================================================
# DOCUMIND AI — TEST RUNNER SCRIPT (WINDOWS POWERSHELL)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Executing DocuMind AI Automated Test Suite         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$env:PYTHONPATH = "backend"
$VenvPytest = "backend\.venv\Scripts\pytest.exe"

if (-not (Test-Path $VenvPytest)) {
    Write-Host "Pytest not found. Run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Run pytest
& $VenvPytest backend\tests -v --durations=10

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All automated tests passed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Test failures detected. Please inspect log above." -ForegroundColor Red
    exit 1
}

