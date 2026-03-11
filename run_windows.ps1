<#
.SYNOPSIS
    VisionPilot main launcher for Windows.

.DESCRIPTION
    Activates the virtual environment, verifies the environment,
    and starts the cleanest runnable path available.

    Default mode: starts all perception microservices directly
    (without Docker) and prints their health status.

    With -BeamNG: also launches the BeamNG simulation loop.

.PARAMETER Mode
    'services'  – start perception microservices only (default)
    'beamng'    – start microservices + BeamNG simulation
    'verify'    – only run environment checks, do not start anything

.PARAMETER BeamNGHome
    Path to BeamNG.tech install folder (or set BEAMNG_HOME env var).

.PARAMETER SkipVerify
    Skip verify_env.py check at startup.

.EXAMPLE
    .\run_windows.ps1
    .\run_windows.ps1 -Mode beamng -BeamNGHome "C:\BeamNG.tech.v0.37"
    .\run_windows.ps1 -Mode verify
#>

param(
    [ValidateSet('services', 'beamng', 'verify')]
    [string]$Mode = 'services',
    [string]$BeamNGHome = $env:BEAMNG_HOME,
    [switch]$SkipVerify
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# ── Banner ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  VisionPilot – Windows Launcher" -ForegroundColor Cyan
Write-Host "  Mode: $Mode" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ── Activate venv ─────────────────────────────────────────────────────────────
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
    Write-Host "[VisionPilot] Virtual environment activated (.venv)" -ForegroundColor Green
} else {
    Write-Host "[VisionPilot] WARNING: .venv not found – using system Python" -ForegroundColor Yellow
    Write-Host "[VisionPilot] Run .\setup_windows.ps1 first." -ForegroundColor Yellow
}

# ── Verify env ────────────────────────────────────────────────────────────────
if (-not $SkipVerify) {
    Write-Host ""
    Write-Host "[VisionPilot] Running environment verification..." -ForegroundColor Yellow
    python verify_env.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Environment verification FAILED." -ForegroundColor Red
        Write-Host "Run .\setup_windows.ps1 to fix missing dependencies." -ForegroundColor Yellow
        Write-Host "Use -SkipVerify to bypass this check." -ForegroundColor Yellow
        exit 1
    }
}

if ($Mode -eq 'verify') {
    Write-Host ""
    Write-Host "Verification complete. Exiting (verify mode)." -ForegroundColor Green
    exit 0
}

# ── Start services ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[VisionPilot] Starting perception microservices..." -ForegroundColor Yellow
Write-Host ""

$ServiceDefs = @(
    @{ Name = "cv_lane_detection";         Port = 4777; Script = "services\cv_lane_detection_service.py" },
    @{ Name = "object_detection";          Port = 5777; Script = "services\object_detection_service.py"   },
    @{ Name = "traffic_light_detection";   Port = 6777; Script = "services\traffic_light_detection_service.py" },
    @{ Name = "sign_detection";            Port = 7777; Script = "services\sign_detection_service.py"     },
    @{ Name = "sign_classification";       Port = 8777; Script = "services\sign_classification_service.py" },
    @{ Name = "yolop";                     Port = 9777; Script = "services\yolop_service.py"              }
)

$ServiceProcs = @()

foreach ($svc in $ServiceDefs) {
    Write-Host "  Starting $($svc.Name) on port $($svc.Port)..." -NoNewline
    $proc = Start-Process -FilePath "python" `
        -ArgumentList $svc.Script `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput "logs\$($svc.Name).log" `
        -RedirectStandardError  "logs\$($svc.Name).err" `
        -ErrorAction SilentlyContinue

    if ($proc) {
        $ServiceProcs += $proc
        Write-Host " PID $($proc.Id)" -ForegroundColor Green
    } else {
        Write-Host " FAILED to start" -ForegroundColor Red
    }
}

# ── Wait for services to initialise ──────────────────────────────────────────
Write-Host ""
Write-Host "[VisionPilot] Waiting 5 s for services to initialise..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# ── Health check ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[VisionPilot] Checking service health..." -ForegroundColor Yellow
Write-Host ""

$AllHealthy = $true
foreach ($svc in $ServiceDefs) {
    $url = "http://localhost:$($svc.Port)/health"
    try {
        $resp = Invoke-RestMethod -Uri $url -TimeoutSec 3 -ErrorAction Stop
        Write-Host "  [OK]  $($svc.Name)  http://localhost:$($svc.Port)" -ForegroundColor Green
    } catch {
        Write-Host "  [!!]  $($svc.Name)  http://localhost:$($svc.Port)  – not responding" -ForegroundColor Yellow
        $AllHealthy = $false
    }
}

Write-Host ""
if ($AllHealthy) {
    Write-Host "[VisionPilot] All services healthy." -ForegroundColor Green
} else {
    Write-Host "[VisionPilot] Some services not yet healthy." -ForegroundColor Yellow
    Write-Host "              Services that need MODEL_PATH (object det, sign, traffic light, yolop)" -ForegroundColor Yellow
    Write-Host "              will only start when model .pt files are present in models/." -ForegroundColor Yellow
    Write-Host "              CV lane detection (port 4777) should be healthy without models." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Service logs are in the logs\ folder." -ForegroundColor White

if ($Mode -eq 'services') {
    Write-Host ""
    Write-Host "Services are running in the background." -ForegroundColor Green
    Write-Host "Press Enter to stop all services." -ForegroundColor Yellow
    Read-Host | Out-Null
}

# ── BeamNG mode ───────────────────────────────────────────────────────────────
if ($Mode -eq 'beamng') {
    Write-Host ""
    if (-not $BeamNGHome) {
        Write-Host "ERROR: -BeamNGHome not set and BEAMNG_HOME env var is empty." -ForegroundColor Red
        Write-Host "       Set it with:  `$env:BEAMNG_HOME = 'C:\Path\To\BeamNG.tech'" -ForegroundColor Yellow
    } elseif (-not (Test-Path $BeamNGHome)) {
        Write-Host "ERROR: BeamNG home not found: $BeamNGHome" -ForegroundColor Red
    } else {
        $env:BEAMNG_HOME = $BeamNGHome
        Write-Host "[VisionPilot] Starting BeamNG simulation..." -ForegroundColor Yellow
        Write-Host "              Press Ctrl+C to stop" -ForegroundColor White
        python simulation\beamng.py
    }
}

# ── Shutdown ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[VisionPilot] Stopping services..." -ForegroundColor Yellow
foreach ($proc in $ServiceProcs) {
    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "[VisionPilot] Done." -ForegroundColor Green
