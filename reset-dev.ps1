# ==============================================================================
# DOCUMIND AI — RESET DEVELOPMENT ENVIRONMENT SCRIPT (WINDOWS POWERSHELL)
# ==============================================================================

Write-Host "Resetting DocuMind AI development state..." -ForegroundColor Yellow

# Remove SQLite DB
if (Test-Path "documind.db") {
    Remove-Item "documind.db" -Force
    Write-Host "Removed documind.db" -ForegroundColor Green
}

if (Test-Path "test_documind.db") {
    Remove-Item "test_documind.db" -Force
    Write-Host "Removed test_documind.db" -ForegroundColor Green
}

# Clean uploads directory
if (Test-Path "storage\uploads") {
    Get-ChildItem "storage\uploads" -Exclude ".gitkeep" | Remove-Item -Recurse -Force
    Write-Host "Cleaned storage/uploads directory" -ForegroundColor Green
}

# Re-generate synthetic test invoices
$env:PYTHONPATH = "backend"
$VenvPython = "backend\.venv\Scripts\python.exe"

Write-Host "Regenerating synthetic invoice dataset..." -ForegroundColor Cyan
& $VenvPython scripts\generate_synthetic_invoices.py

Write-Host "Re-seeding database with demonstration entities..." -ForegroundColor Cyan
& $VenvPython scripts\seed_db.py

Write-Host ""
Write-Host "Development environment reset cleanly!" -ForegroundColor Green
