# ===== 一键停止多 Agent 聊天系统 =====
$ErrorActionPreference = "SilentlyContinue"

Write-Host "[stop] killing uvicorn backend ..." -ForegroundColor Yellow
Get-Process | Where-Object {
    $_.Path -like "*.venv*python*.exe" -or
    $_.CommandLine -like "*uvicorn*main:app*" -or
    $_.CommandLine -like "*uvicorn*backend.main:app*"
} | Stop-Process -Force

Write-Host "[stop] killing vite dev server ..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*vite*" -or $_.Path -like "*frontend\node_modules*"
} | Stop-Process -Force

Write-Host "[stop] killing backend/frontend window titles ..." -ForegroundColor Yellow
taskkill /F /FI "WINDOWTITLE eq backend*"  2>$null
taskkill /F /FI "WINDOWTITLE eq frontend*" 2>$null

Write-Host "[stop] done." -ForegroundColor Green
