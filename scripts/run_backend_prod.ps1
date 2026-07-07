# 生产模式启动 FastAPI（无 reload，workers=1）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ports = Get-Content "$Root\src\backend\config\ports.json" -Raw | ConvertFrom-Json

Remove-Item Env:HTTP_PROXY, Env:HTTPS_PROXY, Env:http_proxy, Env:https_proxy -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Path "data\logs", "data\diagrams" -Force | Out-Null

if (-not $env:APP_ENV) { $env:APP_ENV = "production" }
if (-not $env:LOG_FORMAT) { $env:LOG_FORMAT = "json" }

Write-Host "APP_ENV=$env:APP_ENV  Backend: http://$($ports.backend.host):$($ports.backend.port)" -ForegroundColor Cyan
Write-Host "部署说明: docs/DEPLOYMENT.md" -ForegroundColor Yellow

& .\.venv\Scripts\python.exe -m backend.cli
