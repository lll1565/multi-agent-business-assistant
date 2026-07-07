# 启动 FastAPI 后端 (从项目根运行, 使用 backend.main:app)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ports = Get-Content "$Root\src\backend\config\ports.json" -Raw | ConvertFrom-Json
$backendPort = $ports.backend.port
$uvicornHost = $ports.backend.uvicorn_host

Remove-Item Env:HTTP_PROXY  -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy  -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Path "data\logs"   -Force | Out-Null
New-Item -ItemType Directory -Path "data\diagrams" -Force | Out-Null

if (-not $env:LOG_LEVEL) { $env:LOG_LEVEL = "INFO" }
Write-Host "LOG_LEVEL=$env:LOG_LEVEL  log file: $Root\data\logs\app.log" -ForegroundColor Cyan
Write-Host "Backend: http://$($ports.backend.host):$backendPort" -ForegroundColor Cyan

& python -m uvicorn backend.main:app `
    --host $uvicornHost `
    --port $backendPort `
    --reload `
    --reload-dir src/backend `
    --log-level $env:LOG_LEVEL.ToLower()
