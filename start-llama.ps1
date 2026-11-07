param([string]$ModelPath = "", [int]$Port = 8080, [int]$ContextSize = 8192, [switch]$CpuOnly)
$ErrorActionPreference = "Stop"
$llamaServer = Get-Command llama-server -CommandType Application -ErrorAction SilentlyContinue
if (-not $llamaServer) { throw "llama-server is missing from PATH. Install llama.cpp, then open a new PowerShell terminal." }
if (-not $ModelPath) {
    $modelCache = Join-Path $env:USERPROFILE ".cache\huggingface\hub\models--unsloth--gemma-4-12B-it-qat-GGUF\snapshots"
    if (Test-Path -LiteralPath $modelCache) {
        $cachedModel = Get-ChildItem -LiteralPath $modelCache -Recurse -File -Filter "gemma-4-12B-it-qat-UD-Q4_K_XL.gguf" | Sort-Object FullName | Select-Object -First 1
        if ($cachedModel) { $ModelPath = $cachedModel.FullName }
    }
}
if (-not $ModelPath -or -not (Test-Path -LiteralPath $ModelPath -PathType Leaf)) {
    throw "Gemma GGUF not found. Pass -ModelPath 'D:\models\your-model.gguf' to use the installed file."
}
Write-Host "Loading installed Gemma GGUF: $ModelPath"
Write-Host "Keep this terminal running. Wait for server readiness, then start the website."
$previousGraphSetting = $env:GGML_VK_DISABLE_GRAPH_OPTIMIZE
# This installed Vulkan/NVIDIA combination crashed on successive requests without this setting.
# Scope the workaround to this process and its child; leave the user's driver settings alone.
$env:GGML_VK_DISABLE_GRAPH_OPTIMIZE = "1"
$modelArgs = @('--model', $ModelPath, '--alias', 'gemma-4-12b', '--host', '127.0.0.1',
    '--port', "$Port", '--ctx-size', "$ContextSize", '--parallel', '1', '--jinja', '--reasoning', 'off',
    '--no-cache-prompt', '--cache-ram', '0', '--ctx-checkpoints', '0', '--batch-size', '256', '--ubatch-size', '128')
if ($CpuOnly) { $modelArgs += @('--gpu-layers', '0', '--device', 'none') }
else { $modelArgs += @('--gpu-layers', 'all') }
try {
    & $llamaServer.Source @modelArgs
    $modelExitCode = $LASTEXITCODE
} finally {
    $env:GGML_VK_DISABLE_GRAPH_OPTIMIZE = $previousGraphSetting
}
exit $modelExitCode
