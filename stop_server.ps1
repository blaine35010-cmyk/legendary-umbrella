<#
Stop the local server started by `run_server.ps1`.

Behavior:
- If `web/server.pid` exists, try to stop that PID.
- Otherwise, find processes with `simple_server.py` or `uvicorn` in their command line and stop them.
- Removes `web/server.port` and `web/server.pid` files when possible.

Usage:
  ./stop_server.ps1
#>

Set-StrictMode -Version Latest
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $RepoRoot

$pidFile = Join-Path $RepoRoot "web\server.pid"
$portFile = Join-Path $RepoRoot "web\server.port"

function TryStopPid([int]$pid) {
    try {
        Write-Output "Stopping PID $pid..."
        Stop-Process -Id $pid -Force -ErrorAction Stop
        Write-Output "Stopped $pid"
        return $true
    } catch {
        Write-Warning ("Failed to stop $($pid): {0}" -f $_)
        return $false
    }
}

$stopped = $false
if (Test-Path $pidFile) {
    try {
        $pid = [int](Get-Content $pidFile -ErrorAction Stop)
        $stopped = TryStopPid $pid
    } catch {
        Write-Warning "Could not read PID file: $_"
    }
}

if (-not $stopped) {
    # fallback: find python processes with simple_server.py or uvicorn
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'simple_server.py|uvicorn' }
    if ($procs) {
        foreach ($p in $procs) {
            TryStopPid $p.ProcessId | Out-Null
            $stopped = $true
        }
    } else {
        Write-Output "No matching server processes found."
    }
}

# cleanup files
if (Test-Path $pidFile) { Remove-Item $pidFile -ErrorAction SilentlyContinue }
if (Test-Path $portFile) { Remove-Item $portFile -ErrorAction SilentlyContinue }

if ($stopped) { Write-Output "Server stop attempted." } else { Write-Output "No server stopped." }

Pop-Location
