# PowerShell version for Windows

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir\..

$CarlaProcess = $null

try {
    Write-Host "Starting CARLA..."
    $CarlaProcess = Start-Process -FilePath "C:\Users\user\Documents\CARLA_0.9.16\CarlaUE4.exe" -PassThru

    Start-Sleep -Seconds 5

    Write-Host "Starting simulation..."
    python simulation\run_carla.py
}
finally {
    Write-Host "Shutting down..."
    if ($CarlaProcess) {
        Stop-Process -Id $CarlaProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
