# ============================================================
# start.ps1 -- One-command startup for Windows (PowerShell)
# Usage:  .\start.ps1
#    or:  $env:GEMINI_API_KEY="your_key"; .\start.ps1   (live mode)
# ============================================================

Write-Host ""
Write-Host "  ====================================================" -ForegroundColor Cyan
Write-Host "    Enterprise Agent Trust & Evaluation Platform" -ForegroundColor Cyan
Write-Host "    Agentic Commerce Reliability & Recovery Lab" -ForegroundColor Cyan
Write-Host "  ====================================================" -ForegroundColor Cyan
Write-Host ""

# Copy .env if missing
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[setup] Created .env from .env.example" -ForegroundColor Yellow
}

# Set mode
if ($env:GEMINI_API_KEY) {
    Write-Host "[mode] LIVE mode -- Using Gemini API" -ForegroundColor Green
} else {
    Write-Host "[mode] DEMO mode -- Using deterministic mock (no API key needed)" -ForegroundColor Blue
}

# Set Next.js env
Set-Content -Path "apps\web\.env.local" -Value "NEXT_PUBLIC_API_URL=http://localhost:8000"

# Setup Python venv
if (-not (Test-Path ".venv")) {
    Write-Host "[setup] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}
& ".venv\Scripts\pip.exe" install -r requirements.txt --quiet

# Setup Node
if (-not (Test-Path "apps\web\node_modules")) {
    Write-Host "[setup] Installing Node.js dependencies..." -ForegroundColor Yellow
    Push-Location "apps\web"; npm install --silent; Pop-Location
}

# Seed database
Write-Host "[db] Seeding database..." -ForegroundColor Yellow
& ".venv\Scripts\python.exe" -m apps.api.app.db.seed_data

# Start API
Write-Host "[api] Starting FastAPI on http://localhost:8000 ..." -ForegroundColor Cyan
$apiJob = Start-Process -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000" `
    -PassThru -WindowStyle Hidden

# Wait for API
Write-Host "[api] Waiting for API to be ready..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health/live" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        $ready = $true; break
    } catch { Start-Sleep -Seconds 1 }
}
if ($ready) { Write-Host "[api] Ready!" -ForegroundColor Green }

# Start Next.js
Write-Host "[web] Starting Next.js on http://localhost:3000 ..." -ForegroundColor Cyan
$webJob = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c cd apps\web && npm run dev" `
    -PassThru -WindowStyle Normal

Start-Sleep -Seconds 5

# Open browser
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "  ====================================================" -ForegroundColor Green
Write-Host "    ENTERPRISE AI PLATFORM IS RUNNING" -ForegroundColor Green
Write-Host "  ====================================================" -ForegroundColor Green
Write-Host "    Dashboard:  http://localhost:3000" -ForegroundColor White
Write-Host "    API Docs:   http://localhost:8000/docs" -ForegroundColor White
if ($env:GEMINI_API_KEY) {
    Write-Host "    Mode:       LIVE (Gemini API)" -ForegroundColor Green
} else {
    Write-Host "    Mode:       DEMO (Mock - fully offline)" -ForegroundColor Blue
}
Write-Host "  ====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Press Ctrl+C or close this window to stop." -ForegroundColor Yellow

Write-Host "  API PID: $($apiJob.Id) | Web PID: $($webJob.Id)" -ForegroundColor DarkGray

try { Wait-Process -Id $apiJob.Id } catch {}