<#
.SYNOPSIS
    Start VisionPilot perception microservices directly (without Docker).

.DESCRIPTION
    Launches each Flask service in a background job, waits for them to
    initialise, then prints a health summary.

    This is the Windows equivalent of scripts/start_services.sh.
    Services that require model weights (object_detection, traffic_light,
    sign_detection, sign_classification, yolop) will start but return
    unhealthy until the corresponding .pt / .h5 files exist in models/.

    CV lane detection (port 4777) works without any model files.

.PARAMETER WaitSeconds
    Seconds to wait after starting services before health check (default 8).

.EXAMPLE
    .\scripts\start_services.ps1
    .\scripts\start_services.ps1 -WaitSeconds 15
#>

param(
    [int]$WaitSeconds = 8
)

$ScriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot  = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Activate venv
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) { . $VenvActivate }

# Ensure logs directory exists
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  VisionPilot Perception Services" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$ServiceDefs = @(
    @{ Name = "cv_lane_detection";         Port = 4777; Script = "services\cv_lane_detection_service.py";         Env = @{} },
    @{ Name = "object_detection";          Port = 5777; Script = "services\object_detection_service.py";           Env = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\object_detection\object_detection.pt") } },
    @{ Name = "traffic_light_detection";   Port = 6777; Script = "services\traffic_light_detection_service.py";   Env = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\traffic_light\traffic_light_detection.pt") } },
    @{ Name = "sign_detection";            Port = 7777; Script = "services\sign_detection_service.py";             Env = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\traffic_sign\traffic_sign_detection.pt") } },
    @{ Name = "sign_classification";       Port = 8777; Script = "services\sign_classification_service.py";       Env = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\traffic_sign\traffic_sign_classification.h5") } },
    @{ Name = "yolop";                     Port = 9777; Script = "services\yolop_service.py";                     Env = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\yolop\yolop.pt") } }
)

$Procs = @()

foreach ($svc in $ServiceDefs) {
    $logFile = Join-Path $LogDir "$($svc.Name).log"
    $errFile = Join-Path $LogDir "$($svc.Name).err"

    # Set per-service env vars
    foreach ($key in $svc.Env.Keys) {
        [System.Environment]::SetEnvironmentVariable($key, $svc.Env[$key], "Process")
    }

    Write-Host "  Starting $($svc.Name) (port $($svc.Port))..." -NoNewline

    $proc = Start-Process -FilePath "python" `
        -ArgumentList $svc.Script `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError  $errFile `
        -ErrorAction SilentlyContinue

    if ($proc) {
        $Procs += @{ Proc = $proc; Name = $svc.Name; Port = $svc.Port }
        Write-Host " PID $($proc.Id)" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Waiting $WaitSeconds seconds for services to initialise..." -ForegroundColor Yellow
Start-Sleep -Seconds $WaitSeconds

Write-Host ""
Write-Host "Service Health Check:" -ForegroundColor Yellow
Write-Host ""

$AllHealthy = $true
foreach ($item in $Procs) {
    $url = "http://localhost:$($item.Port)/health"
    try {
        Invoke-RestMethod -Uri $url -TimeoutSec 3 -ErrorAction Stop | Out-Null
        Write-Host "  [OK]  $($item.Name)   http://localhost:$($item.Port)" -ForegroundColor Green
    } catch {
        $log = Join-Path $LogDir "$($item.Name).err"
        Write-Host "  [!!]  $($item.Name)   http://localhost:$($item.Port)  – not responding" -ForegroundColor Yellow
        if (Test-Path $log) {
            $lastErr = Get-Content $log -Tail 3 | Where-Object { $_.Trim() -ne "" } | Select-Object -Last 1
            if ($lastErr) { Write-Host "        Last error: $lastErr" -ForegroundColor DarkYellow }
        }
        $AllHealthy = $false
    }
}

Write-Host ""
if ($AllHealthy) {
    Write-Host "All services healthy!" -ForegroundColor Green
} else {
    Write-Host "Some services did not respond." -ForegroundColor Yellow
    Write-Host "Services needing model files will show unhealthy until .pt/.h5 files" -ForegroundColor Yellow
    Write-Host "are placed in the models/ directory." -ForegroundColor Yellow
    Write-Host "Check logs\ for details." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Service logs : $LogDir" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services run:" -ForegroundColor Yellow
Write-Host "  Get-Process python | Stop-Process" -ForegroundColor Cyan
Write-Host ""
