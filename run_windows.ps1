<#
.SYNOPSIS
    VisionPilot main launcher for Windows.

.DESCRIPTION
    Activates the virtual environment, verifies the environment,
    and starts the perception microservices.

    DEFAULT MODE ('services'):
      Starts only the CV lane detection service (port 4777).
      This is the ONLY service that works without model weight files.
      It always produces a healthy /health response on a clean install.

      To start ALL services (requires model .pt/.h5 files for most):
        .\run_windows.ps1 -Mode all-services

    OTHER MODES:
      'beamng'   - start all services + BeamNG.tech simulation loop
                   (requires BeamNG.tech licence + BEAMNG_HOME env var)
      'verify'   - environment check only, nothing started

    PRIMARY SIMULATOR: BeamNG.tech
      CARLA integration is not yet implemented in this repo.
      BeamNG is the only runnable simulator path.

.PARAMETER Mode
    'services'      - start CV lane detection service only (default, always works)
    'all-services'  - start all 6 perception services (needs model files for most)
    'beamng'        - start all services + BeamNG simulation
    'verify'        - run environment checks only

.PARAMETER BeamNGHome
    Path to BeamNG.tech install folder (or set BEAMNG_HOME env var).

.PARAMETER SkipVerify
    Skip verify_env.py check at startup.

.EXAMPLE
    .\run_windows.ps1
    .\run_windows.ps1 -Mode all-services
    .\run_windows.ps1 -Mode beamng -BeamNGHome "C:\BeamNG.tech.v0.37"
    .\run_windows.ps1 -Mode verify
#>

param(
    [ValidateSet('services', 'all-services', 'beamng', 'verify')]
    [string]$Mode = 'services',
    [string]$BeamNGHome = $env:BEAMNG_HOME,
    [switch]$SkipVerify
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "logs") | Out-Null

# Banner
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  VisionPilot - Windows Launcher" -ForegroundColor Cyan
Write-Host "  Mode: $Mode" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Activate venv
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
    Write-Host "[VisionPilot] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[VisionPilot] WARNING: .venv not found - using system Python" -ForegroundColor Yellow
    Write-Host "             Run .\setup_windows.ps1 first for a clean install." -ForegroundColor Yellow
}

# Verify env
if (-not $SkipVerify) {
    Write-Host ""
    Write-Host "[VisionPilot] Checking environment..." -ForegroundColor Yellow
    python verify_env.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Environment check FAILED. Run .\setup_windows.ps1 to fix." -ForegroundColor Red
        Write-Host "Use -SkipVerify to bypass this check (not recommended)." -ForegroundColor Yellow
        exit 1
    }
}

if ($Mode -eq 'verify') {
    Write-Host ""
    Write-Host "Verification complete. Nothing started (verify mode)." -ForegroundColor Green
    exit 0
}

# Service catalog
$ServiceDefs = @(
    @{
        Name        = "cv_lane_detection"
        Port        = 4777
        Script      = "services\cv_lane_detection_service.py"
        Tier        = "always-on"
        Env         = @{}
        ModelPath   = $null
        Description = "OpenCV lane detection - no model file required"
    },
    @{
        Name        = "object_detection"
        Port        = 5777
        Script      = "services\object_detection_service.py"
        Tier        = "needs-model"
        Env         = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\object_detection\object_detection.pt") }
        ModelPath   = (Join-Path $ProjectRoot "models\object_detection\object_detection.pt")
        Description = "YOLOv11 object detection"
    },
    @{
        Name        = "traffic_light_detection"
        Port        = 6777
        Script      = "services\traffic_light_detection_service.py"
        Tier        = "needs-model"
        Env         = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\traffic_light\traffic_light_detection.pt") }
        ModelPath   = (Join-Path $ProjectRoot "models\traffic_light\traffic_light_detection.pt")
        Description = "YOLOv11 traffic light detection"
    },
    @{
        Name        = "sign_detection"
        Port        = 7777
        Script      = "services\sign_detection_service.py"
        Tier        = "needs-model"
        Env         = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\traffic_sign\traffic_sign_detection.pt") }
        ModelPath   = (Join-Path $ProjectRoot "models\traffic_sign\traffic_sign_detection.pt")
        Description = "YOLOv11 traffic sign detection"
    },
    @{
        Name        = "sign_classification"
        Port        = 8777
        Script      = "services\sign_classification_service.py"
        Tier        = "needs-model"
        Env         = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\traffic_sign\traffic_sign_classification.h5") }
        ModelPath   = (Join-Path $ProjectRoot "models\traffic_sign\traffic_sign_classification.h5")
        Description = "CNN sign classification"
    },
    @{
        Name        = "yolop"
        Port        = 9777
        Script      = "services\yolop_service.py"
        Tier        = "needs-model"
        Env         = @{ MODEL_PATH = (Join-Path $ProjectRoot "models\yolop\yolop.pt") }
        ModelPath   = (Join-Path $ProjectRoot "models\yolop\yolop.pt")
        Description = "YOLOP unified perception"
    }
)

# Decide which services to start
switch ($Mode) {
    'services'     { $ToStart = $ServiceDefs | Where-Object { $_.Tier -eq 'always-on' } }
    'all-services' { $ToStart = $ServiceDefs }
    'beamng'       { $ToStart = $ServiceDefs }
}

# Print model availability for all-services / beamng modes
if ($Mode -ne 'services') {
    Write-Host ""
    Write-Host "Model file status:" -ForegroundColor Yellow
    foreach ($svc in $ServiceDefs | Where-Object { $_.Tier -eq 'needs-model' }) {
        if ($svc.ModelPath -and (Test-Path $svc.ModelPath)) {
            Write-Host "  [OK] $($svc.Name)" -ForegroundColor Green
        } else {
            Write-Host "  [!!] $($svc.Name) - model not found, service exits at startup" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Start services
Write-Host "[VisionPilot] Starting services..." -ForegroundColor Yellow
Write-Host ""

$ServiceProcs = @()

foreach ($svc in $ToStart) {
    Write-Host "  $($svc.Name)  :$($svc.Port)  $($svc.Description)" -NoNewline

    foreach ($key in $svc.Env.Keys) {
        [System.Environment]::SetEnvironmentVariable($key, $svc.Env[$key], "Process")
    }

    $logOut = Join-Path $ProjectRoot "logs\$($svc.Name).log"
    $logErr = Join-Path $ProjectRoot "logs\$($svc.Name).err"

    $proc = Start-Process -FilePath "python" `
        -ArgumentList $svc.Script `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $logOut `
        -RedirectStandardError  $logErr `
        -ErrorAction SilentlyContinue

    if ($proc) {
        $ServiceProcs += $proc
        Write-Host "  [PID $($proc.Id)]" -ForegroundColor Green
    } else {
        Write-Host "  [FAILED]" -ForegroundColor Red
    }
}

# Health check
Write-Host ""
Write-Host "[VisionPilot] Waiting for services to initialise..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host ""
Write-Host "Health check:" -ForegroundColor Yellow
Write-Host ""

foreach ($svc in $ToStart) {
    $url = "http://localhost:$($svc.Port)/health"
    try {
        Invoke-RestMethod -Uri $url -TimeoutSec 3 -ErrorAction Stop | Out-Null
        Write-Host "  [OK]  $($svc.Name)   http://localhost:$($svc.Port)" -ForegroundColor Green
    } catch {
        Write-Host "  [!!]  $($svc.Name)   http://localhost:$($svc.Port)  - not responding" -ForegroundColor Yellow
    }
}

Write-Host ""

if ($Mode -eq 'services') {
    Write-Host "CV lane detection is live at http://localhost:4777" -ForegroundColor Green
    Write-Host ""
    Write-Host "  GET  http://localhost:4777/health   -- health check" -ForegroundColor White
    Write-Host "  POST http://localhost:4777/process  -- process a frame" -ForegroundColor White
    Write-Host ""
    Write-Host "To start all 6 services: .\run_windows.ps1 -Mode all-services" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Enter to stop." -ForegroundColor Yellow
    Read-Host | Out-Null

} elseif ($Mode -eq 'all-services') {
    Write-Host "All services started. Services without model files show [!!] above." -ForegroundColor Yellow
    Write-Host "Place model weights in models\ to enable those services." -ForegroundColor Yellow
    Write-Host "See docs\WINDOWS_SETUP.md for details." -ForegroundColor White
    Write-Host ""
    Write-Host "Press Enter to stop all services." -ForegroundColor Yellow
    Read-Host | Out-Null
}

# BeamNG mode
if ($Mode -eq 'beamng') {
    Write-Host ""
    if (-not $BeamNGHome) {
        Write-Host "ERROR: BeamNG.tech home not specified." -ForegroundColor Red
        Write-Host "  Set BEAMNG_HOME: `$env:BEAMNG_HOME = 'C:\Path\To\BeamNG.tech.vX.X'" -ForegroundColor Yellow
    } elseif (-not (Test-Path $BeamNGHome)) {
        Write-Host "ERROR: BeamNG home directory not found: $BeamNGHome" -ForegroundColor Red
    } else {
        $env:BEAMNG_HOME = $BeamNGHome
        Write-Host "[VisionPilot] Starting BeamNG simulation loop..." -ForegroundColor Yellow
        Write-Host "             BeamNG home: $BeamNGHome" -ForegroundColor White
        Write-Host "             Press Ctrl+C to stop" -ForegroundColor White
        Write-Host ""
        python simulation\beamng.py
    }
}

# Shutdown
Write-Host ""
Write-Host "[VisionPilot] Stopping services..." -ForegroundColor Yellow
foreach ($proc in $ServiceProcs) {
    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "[VisionPilot] Done. Logs: .\logs\" -ForegroundColor Green
Write-Host ""
