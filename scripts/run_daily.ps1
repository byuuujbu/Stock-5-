$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$StdoutLog = Join-Path $LogDir "daily-$Timestamp.out.log"
$StderrLog = Join-Path $LogDir "daily-$Timestamp.err.log"

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "py"
}
if ($Python -eq "py" -and -not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    $BundledPython = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $BundledPython) {
        $Python = $BundledPython
    } else {
        throw "Python was not found. Install Python 3.11+ or update scripts/run_daily.ps1."
    }
}

$Command = "`"$Python`" -m app.agent 1> `"$StdoutLog`" 2> `"$StderrLog`""
cmd.exe /d /c $Command
$ExitCode = $LASTEXITCODE
if ($ExitCode -ne 0) {
    throw "Daily agent failed with exit code $ExitCode. See $StdoutLog and $StderrLog."
}
