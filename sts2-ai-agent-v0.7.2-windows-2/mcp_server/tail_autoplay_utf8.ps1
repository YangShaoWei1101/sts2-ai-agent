[CmdletBinding()]
param(
    [ValidateSet("log", "journal", "summary", "stdout", "stderr")]
    [string]$Kind = "log",
    [int]$Tail = 200,
    [switch]$Wait
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

$Files = @{
    log = "autoplay_ironclad.log"
    journal = "autoplay_decision_journal.jsonl"
    summary = "autoplay_ironclad_summary.json"
    stdout = "autoplay_run.out.log"
    stderr = "autoplay_run.err.log"
}

$Target = Join-Path $ScriptDir $Files[$Kind]
if (-not (Test-Path -LiteralPath $Target)) {
    throw "Log file not found: $Target"
}

if ($Wait) {
    Get-Content -LiteralPath $Target -Encoding UTF8 -Tail $Tail -Wait
} else {
    Get-Content -LiteralPath $Target -Encoding UTF8 -Tail $Tail
}
