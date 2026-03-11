# PowerShell launcher for VisionPilot BeamNG simulation
# Usage: .\scripts\start_simulation.ps1 [-BeamNGHome <path>] [-Map <name>] [-Scenario <type>]

param(
    [string]$BeamNGHome = $env:BEAMNG_HOME,
    [string]$Map = "west_coast_usa",
    [string]$Scenario = "highway"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Activate virtual environment if present
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
    Write-Host "[VisionPilot] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[VisionPilot] No .venv found - using system Python" -ForegroundColor Yellow
    Write-Host "[VisionPilot] Run setup_windows.ps1 first for best results" -ForegroundColor Yellow
}

# Validate BeamNG home
if (-not $BeamNGHome) {
    Write-Host ""
    Write-Host "ERROR: BeamNG.tech installation not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set the BEAMNG_HOME environment variable or pass -BeamNGHome:" -ForegroundColor Yellow
    Write-Host "  `$env:BEAMNG_HOME = 'C:\Path\To\BeamNG.tech.v0.37.x.x'" -ForegroundColor Cyan
    Write-Host "  .\scripts\start_simulation.ps1 -BeamNGHome 'C:\Path\To\BeamNG.tech'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can also set BEAMNG_HOME in config\beamng_sim.yaml under simulation.home" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $BeamNGHome)) {
    Write-Host "ERROR: BeamNG home directory not found: $BeamNGHome" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  VisionPilot - BeamNG Simulation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  BeamNG Home : $BeamNGHome" -ForegroundColor White
Write-Host "  Map         : $Map" -ForegroundColor White
Write-Host "  Scenario    : $Scenario" -ForegroundColor White
Write-Host ""

# Update beamng_sim.yaml with resolved path if env var used
$env:BEAMNG_HOME = $BeamNGHome

Write-Host "[VisionPilot] Starting BeamNG simulation..." -ForegroundColor Green
Write-Host "[VisionPilot] Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python simulation\beamng.py
