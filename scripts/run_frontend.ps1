$ErrorActionPreference = "Stop"

# scripts 目录；正常脚本执行时 $PSScriptRoot 即为 scripts 目录。
$ScriptDir = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($ScriptDir)) {
    $ScriptFile = $MyInvocation.MyCommand.Path
    if ([string]::IsNullOrWhiteSpace($ScriptFile)) {
        Write-Error "无法获取 run_frontend.ps1 的脚本路径。请直接运行 .\scripts\run_frontend.ps1"
        exit 1
    }
    $ScriptDir = Split-Path -Parent $ScriptFile
}

# scripts 的上一级就是项目根目录。
$ProjectRoot = Split-Path -Parent $ScriptDir

# 前端目录和 package.json。
$FrontendDir = Join-Path $ProjectRoot "frontend"
$PackageJson = Join-Path $FrontendDir "package.json"

if (-not (Test-Path -LiteralPath $PackageJson -PathType Leaf)) {
    Write-Error "未找到前端 package.json：$PackageJson"
    exit 1
}

Write-Host "Frontend directory: $FrontendDir"
Write-Host "Frontend: http://127.0.0.1:5143"

Set-Location -LiteralPath $FrontendDir
npm run dev

exit $LASTEXITCODE
