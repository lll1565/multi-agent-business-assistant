# 启动 Vue 前端（需先 npm install）
$Root = Split-Path -Parent $PSScriptRoot
Set-Location "$Root\frontend"
npm run dev
