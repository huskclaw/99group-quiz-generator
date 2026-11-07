param([int]$Port = 8501, [switch]$Lan)
$ErrorActionPreference = "Stop"
$projectPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $projectPython -PathType Leaf)) {
    throw "Project environment missing. Run setup.ps1 first (see README.md)."
}
$bindAddress = if ($Lan) { "0.0.0.0" } else { "127.0.0.1" }
Push-Location $PSScriptRoot
try {
    & $projectPython -m streamlit run app.py --server.address $bindAddress --server.port $Port --server.headless true --browser.gatherUsageStats false
    exit $LASTEXITCODE
} finally { Pop-Location }
