# KisaanVaani Fast Start Script
# Usage: ./run.ps1

Write-Host "🚀 Cleaning up existing ports (8000, 5174)..." -ForegroundColor Cyan

# Kill existing processes (node, uvicorn, python)
Get-Process -Name uvicorn, node, python -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill by ports specifically to be sure
$p8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($p8000) { Stop-Process -Id $p8000.OwningProcess -Force }

$p5174 = Get-NetTCPConnection -LocalPort 5174 -ErrorAction SilentlyContinue
if ($p5174) { Stop-Process -Id $p5174.OwningProcess -Force }

Write-Host "✅ Ports cleared." -ForegroundColor Green

Write-Host "📦 Starting Backend Server (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "🌐 Starting Frontend Server (Port 5174)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev -- --host"

Write-Host "🎉 Servers are starting! Check the new terminal windows." -ForegroundColor Green
Write-Host "🔗 Frontend: http://localhost:5174" -ForegroundColor White
Write-Host "🔗 Backend:  http://localhost:8000" -ForegroundColor White