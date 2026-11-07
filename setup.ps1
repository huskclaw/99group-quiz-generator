param([string]$PythonPath = "")
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    if ($PythonPath) {
        & $PythonPath -m venv .venv
    } elseif (Get-Command uv -CommandType Application -ErrorAction SilentlyContinue) {
        & uv venv --python 3.11 .venv
    } else {
        & py -3.11 -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw "Could not create Python environment. Install Python 3.11+ or pass -PythonPath." }
    $projectPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Get-Command uv -CommandType Application -ErrorAction SilentlyContinue) {
        & uv pip install --python $projectPython -r requirements-dev.txt
    } else {
        & $projectPython -m pip install -r requirements-dev.txt
    }
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    Write-Host "Ready. Run start-llama.ps1 and start-web.ps1 in separate terminals."
} finally { Pop-Location }
