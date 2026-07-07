# ===== 一键启动多 Agent 聊天系统 =====
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ports = Get-Content "$Root\src\backend\config\ports.json" -Raw | ConvertFrom-Json
$backendHost = $ports.backend.host
$backendPort = $ports.backend.port
$frontendHost = $ports.frontend.host
$frontendPort = $ports.frontend.port
$frontendUrl = "http://${frontendHost}:${frontendPort}"

Remove-Item Env:HTTP_PROXY  -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy  -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Path "data\logs"     -Force | Out-Null
New-Item -ItemType Directory -Path "data\diagrams" -Force | Out-Null

$env:LOG_LEVEL  = "INFO"
$backendLog = "$Root\data\logs\backend.out.log"
$backendErr = "$Root\data\logs\backend.err.log"

Write-Host "[1/2] Starting backend on http://${backendHost}:${backendPort} ..." -ForegroundColor Cyan
$backend = Start-Process `
    -FilePath "python" `
    -ArgumentList @("-m","uvicorn","backend.main:app","--host",$backendHost,"--port",$backendPort,"--log-level","info") `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError  $backendErr `
    -WindowStyle Hidden `
    -PassThru
Write-Host "      PID = $($backend.Id)  log = $backendLog"

$frontendLog = "$Root\data\logs\frontend.out.log"
$frontendErr = "$Root\data\logs\frontend.err.log"
Write-Host "[2/2] Starting frontend on $frontendUrl ..." -ForegroundColor Cyan
$frontend = Start-Process `
    -FilePath "npm.cmd" `
    -ArgumentList @("run","dev") `
    -WorkingDirectory "$Root\frontend" `
    -RedirectStandardOutput $frontendLog `
    -RedirectStandardError  $frontendErr `
    -WindowStyle Hidden `
    -PassThru
Write-Host "      PID = $($frontend.Id)  log = $frontendLog"

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "=== Health check ===" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "http://${backendHost}:${backendPort}/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  backend  : $($r.StatusCode) - $($r.Content)"
} catch {
    Write-Host "  backend  : DOWN ($($_.Exception.Message))" -ForegroundColor Red
}
try {
    $r = Invoke-WebRequest -Uri "$frontendUrl/" -UseBasicParsing -TimeoutSec 5
    Write-Host "  frontend : $($r.StatusCode)"
} catch {
    Write-Host "  frontend : DOWN ($($_.Exception.Message))" -ForegroundColor Red
}

Write-Host ""
Write-Host "打开浏览器访问：" -ForegroundColor Green
Write-Host "  前端 UI    : $frontendUrl" -ForegroundColor Green
Write-Host "  后端 Swagger: http://${backendHost}:${backendPort}/api/docs" -ForegroundColor Green
Write-Host ""
Write-Host "看实时日志：" -ForegroundColor Yellow
Write-Host "  Get-Content '$Root\data\logs\backend.out.log' -Wait" -ForegroundColor Yellow
Write-Host ""
Write-Host "停止服务：" -ForegroundColor Yellow
Write-Host "  .\scripts\stop_all.ps1" -ForegroundColor Yellow
