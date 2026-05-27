$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

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
        throw "Python was not found. Install Python 3.11+ or update scripts/update_universe.ps1."
    }
}

& $Python .\scripts\update_universe.py
