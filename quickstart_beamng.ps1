<#
.SYNOPSIS
    VisionPilot — one-shot BeamNG setup and launch.

.DESCRIPTION
    Run this once after cloning. It will:
      1. Validate that BeamNG.tech is installed at the given path.
      2. Create the Python virtual environment and install all dependencies
         (including beamngpy).
      3. Persist BEAMNG_HOME to your user environment so you never need to
         set it again.
      4. Launch VisionPilot in BeamNG mode.

    On subsequent runs use:
        .\run_windows.ps1 -Mode beamng

.PARAMETER BeamNGHome
    Path to your BeamNG.tech install folder.
    Example: "C:\Users\Alice\BeamNG.tech.v0.37.6.0"

.PARAMETER SkipSetup
    Skip the venv / dependency installation step.
    Use this on subsequent runs if you only want to re-launch.

.EXAMPLE
    .\quickstart_beamng.ps1 -BeamNGHome "C:\Users\Alice\BeamNG.tech.v0.37.6.0"
    .\quickstart_beamng.ps1 -BeamNGHome "C:\Users\Alice\BeamNG.tech.v0.37.6.0" -SkipSetup
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$BeamNGHome,

    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  VisionPilot — BeamNG Quick-Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Validate BeamNG path ────────────────────────────────────────────────
Write-Host "[1/3] Validating BeamNG path..." -ForegroundColor Yellow

if (-not (Test-Path $BeamNGHome)) {
    Write-Host ""
    Write-Host "ERROR: BeamNG.tech not found at:" -ForegroundColor Red
    Write-Host "       $BeamNGHome" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the path and retry. Example:" -ForegroundColor Yellow
    Write-Host '  .\quickstart_beamng.ps1 -BeamNGHome "C:\Users\YourName\BeamNG.tech.v0.37.6.0"' -ForegroundColor White
    exit 1
}

Write-Host "      Found: $BeamNGHome" -ForegroundColor Green

# ── 2. Setup (venv + deps) ─────────────────────────────────────────────────
if ($SkipSetup) {
    Write-Host "[2/3] Skipping setup (-SkipSetup)." -ForegroundColor Yellow
} else {
    Write-Host "[2/3] Running setup (venv + dependencies + beamngpy)..." -ForegroundColor Yellow
    Write-Host ""
    & "$ProjectRoot\setup_windows.ps1" -WithBeamNG
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Setup failed. Fix the errors above and re-run." -ForegroundColor Red
        exit 1
    }
}

# ── 3. Persist BEAMNG_HOME ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/3] Saving BEAMNG_HOME to your user environment..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable("BEAMNG_HOME", $BeamNGHome, "User")
$env:BEAMNG_HOME = $BeamNGHome
Write-Host "      BEAMNG_HOME = $BeamNGHome" -ForegroundColor Green
Write-Host "      (Persisted — new terminals will inherit this automatically.)" -ForegroundColor White

# ── Launch ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Launching VisionPilot in BeamNG mode..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

& "$ProjectRoot\run_windows.ps1" -Mode beamng -BeamNGHome $BeamNGHome
