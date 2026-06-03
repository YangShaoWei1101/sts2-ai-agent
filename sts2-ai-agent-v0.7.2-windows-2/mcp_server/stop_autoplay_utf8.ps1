[CmdletBinding(SupportsShouldProcess = $true)]
param()

$ErrorActionPreference = "Stop"
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom
try {
    chcp 65001 > $null
} catch {
}

function Get-AutoplayProcess {
    try {
        Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -like "*autoplay_ironclad.py*"
        }
    } catch {
        Get-WmiObject Win32_Process | Where-Object {
            $_.CommandLine -like "*autoplay_ironclad.py*"
        }
    }
}

$Processes = @(Get-AutoplayProcess)
if ($Processes.Count -eq 0) {
    Write-Host "No autoplay_ironclad.py process found."
    exit 0
}

foreach ($Process in $Processes) {
    if ($PSCmdlet.ShouldProcess("PID $($Process.ProcessId)", "Stop autoplay controller")) {
        Stop-Process -Id $Process.ProcessId -Force
        Write-Host "Stopped PID $($Process.ProcessId)"
    }
}
