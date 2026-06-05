[CmdletBinding()]
param(
    [string]$Character = "SILENT",
    [int]$MaxSteps = 1200,
    [int]$Attempts = 1
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom
try {
    chcp 65001 > $null
} catch {
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:STS2_AUTOPLAY_CHARACTER = $Character

$Python = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

& $Python (Join-Path $ScriptDir "autoplay_ironclad.py") --character $Character --max-steps $MaxSteps --attempts $Attempts
exit $LASTEXITCODE
