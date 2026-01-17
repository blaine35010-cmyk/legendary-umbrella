<#
Start the local server (PowerShell).

Behavior:
- Use the project's `.venv` Python if present.
- Set `PYTHONPATH` to the repo root so local imports resolve.
- Prefer `web/simple_server.py` (bundled simple HTTP server). If you prefer
  to run the FastAPI app with Uvicorn, set the environment variable
  `USE_UVICORN=1` before running this script.
- Redirect stdout/stderr to `web/server_stdout.log` / `web/server_stderr.log`.

Usage:
  ./run_server.ps1
  $env:USE_UVICORN=1; ./run_server.ps1
#>

Set-StrictMode -Version Latest
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $RepoRoot

# Find venv python
$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) { $Python = $venvPython } else { $Python = "python" }

# Ensure web log dir exists
New-Item -ItemType Directory -Path (Join-Path $RepoRoot "web") -ErrorAction SilentlyContinue | Out-Null
$outLog = Join-Path $RepoRoot "web\server_stdout.log"
$errLog = Join-Path $RepoRoot "web\server_stderr.log"

# Ensure PYTHONPATH points at the repo
$env:PYTHONPATH = $RepoRoot

if ($env:USE_UVICORN -and $env:USE_UVICORN -ne "0") {
    Write-Output "Starting uvicorn using: $Python"
    $args = @("-m", "uvicorn", "web.app:app", "--host", "127.0.0.1", "--port", "8000")
} else {
    Write-Output "Starting bundled simple server using: $Python"
    $args = @("web/simple_server.py")
}

try {
    $proc = Start-Process -FilePath $Python -ArgumentList $args -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
    Write-Output "Started server process PID=$($proc.Id). Logs: $outLog, $errLog"
} catch {
    Write-Error "Failed to start server: $_"
}

Pop-Location