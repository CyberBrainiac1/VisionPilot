<#
.SYNOPSIS
    VisionPilot Windows setup script.

.DESCRIPTION
    Creates a Python virtual environment, upgrades pip tooling,
    installs all requirements, and runs verify_env.py to confirm
    the installation is healthy.

    Run this once (or after pulling new changes that add dependencies).

.PARAMETER Python
    Path to the python executable to use (default: python).

.PARAMETER RequirementsFile
    Requirements file to install (default: requirements-windows.txt).

.PARAMETER SkipVerify
    Skip running verify_env.py after installation.

.EXAMPLE
    .\setup_windows.ps1
    .\setup_windows.ps1 -Python "C:\Python311\python.exe"
    .\setup_windows.ps1 -SkipVerify
#>

param(
    [string]$Python = "python",
    [string]$RequirementsFile = "requirements-windows.txt",
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  VisionPilot Windows Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Check Python ───────────────────────────────────────────────────────────
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
try {
    $pyVer = & $Python --version 2>&1
    Write-Host "      Found: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "ERROR: '$Python' not found. Install Python 3.9+ and add it to PATH." -ForegroundColor Red
    Write-Host "       Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check version is >= 3.9
$verString = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$major, $minor = $verString.Split('.')
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 9)) {
    Write-Host "ERROR: Python 3.9 or higher is required (found $verString)." -ForegroundColor Red
    exit 1
}

# ── 2. Create / reuse virtual environment ────────────────────────────────────
Write-Host "[2/5] Setting up virtual environment (.venv)..." -ForegroundColor Yellow
$VenvDir = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "      Creating new .venv..." -ForegroundColor White
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "      .venv created." -ForegroundColor Green
} else {
    Write-Host "      .venv already exists, reusing." -ForegroundColor Green
}

# Activate venv
$Activate = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $Activate)) {
    Write-Host "ERROR: Activation script not found at $Activate" -ForegroundColor Red
    exit 1
}
. $Activate
Write-Host "      Virtual environment activated." -ForegroundColor Green

# ── 3. Upgrade pip / setuptools / wheel ──────────────────────────────────────
Write-Host "[3/5] Upgrading pip, setuptools, wheel..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: pip upgrade step had errors – continuing anyway." -ForegroundColor Yellow
}

# ── 4. Install requirements ───────────────────────────────────────────────────
Write-Host "[4/5] Installing requirements from $RequirementsFile..." -ForegroundColor Yellow

if (-not (Test-Path $RequirementsFile)) {
    Write-Host "WARNING: $RequirementsFile not found – falling back to requirements.txt" -ForegroundColor Yellow
    $RequirementsFile = "requirements.txt"
}

# First pass – normal install
python -m pip install -r $RequirementsFile
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Some packages failed to install." -ForegroundColor Yellow
    Write-Host "         Retrying with --no-deps fallback for failed packages..." -ForegroundColor Yellow

    # Retry each package individually so one failure doesn't block everything
    $failed = @()
    Get-Content $RequirementsFile | Where-Object { $_ -notmatch '^\s*#' -and $_.Trim() -ne '' } | ForEach-Object {
        $pkg = $_.Trim()
        python -m pip install $pkg 2>$null
        if ($LASTEXITCODE -ne 0) {
            $failed += $pkg
        }
    }

    if ($failed.Count -gt 0) {
        Write-Host ""
        Write-Host "The following packages could NOT be installed automatically:" -ForegroundColor Red
        $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        Write-Host ""
        Write-Host "Common reasons:" -ForegroundColor Yellow
        Write-Host "  - 'carla' must be installed from a CARLA release wheel" -ForegroundColor Yellow
        Write-Host "  - 'beamngpy' requires a BeamNG.tech licence" -ForegroundColor Yellow
        Write-Host "  See docs/WINDOWS_SETUP.md for manual install instructions." -ForegroundColor Yellow
    }
}

# ── 5. Verify ─────────────────────────────────────────────────────────────────
if (-not $SkipVerify) {
    Write-Host "[5/5] Running environment verification..." -ForegroundColor Yellow
    python verify_env.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Some verification checks FAILED (see output above)." -ForegroundColor Red
        Write-Host "Fix the issues and re-run setup_windows.ps1 or verify_env.py." -ForegroundColor Yellow
    }
} else {
    Write-Host "[5/5] Skipping verification (--SkipVerify)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run diagnostics:  .\diagnose_windows.ps1" -ForegroundColor White
Write-Host "  2. Start services:   .\scripts\start_services.ps1" -ForegroundColor White
Write-Host "  3. Launch app:       .\run_windows.ps1" -ForegroundColor White
Write-Host ""
Write-Host "For BeamNG simulation, also set:" -ForegroundColor Yellow
Write-Host "  `$env:BEAMNG_HOME = 'C:\Path\To\BeamNG.tech.vX.X'" -ForegroundColor Cyan
Write-Host ""
