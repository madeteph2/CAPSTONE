$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (!(Test-Path '.\.venv\Scripts\python.exe')) {
    Write-Error 'Falta .venv. Consulte GUIA_EJECUCION_MICA.md.'
}
& '.\.venv\Scripts\python.exe' manage.py check
if ($LASTEXITCODE -ne 0) { throw 'Fallo manage.py check.' }
& '.\.venv\Scripts\python.exe' manage.py runserver 127.0.0.1:8000
