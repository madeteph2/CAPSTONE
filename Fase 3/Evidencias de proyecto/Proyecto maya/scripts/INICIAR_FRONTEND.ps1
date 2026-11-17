$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'frontend')
if (!(Test-Path '.\node_modules')) { throw 'Falta npm ci. Consulte GUIA_EJECUCION_MICA.md.' }
npm.cmd run dev -- --host 127.0.0.1 --port 5173
