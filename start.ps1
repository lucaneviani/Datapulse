# DataPulse Startup Script (Windows PowerShell)
# Usage: .\start.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DataPulse - AI-Powered Analytics   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$pythonPath = ".\venv\Scripts\python.exe"
if (-Not (Test-Path $pythonPath)) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "Then: pip install -r backend/requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Run the unified launcher which handles env, ports and process startup
Write-Host "Launching DataPulse via scripts/run_local.py" -ForegroundColor Green
& $pythonPath .\scripts\run_local.py

Write-Host "If you prefer the old behavior, edit start.ps1 to your needs." -ForegroundColor Cyan
