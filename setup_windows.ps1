<#
.SYNOPSIS
    VisionPilot Windows setup script.

.DESCRIPTION
    Creates a Python virtual environment, upgrades pip tooling,
    installs all requirements, and runs verify_env.py to confirm
    the installation is healthy.

    RECOMMENDED PYTHON: 3.11
      Python 3.11 has the best Windows wheel coverage for TensorFlow 2.19,
      PyTorch, and OpenCV. Python 3.12 works but some wheels may not exist.
      Python < 3.9 is not supported.

    DEPENDENCY FILE: requirements-windows.txt
      This file removes 'carla' (not on PyPI) and pins numpy<2.0 (required
      by TensorFlow). Do not use requirements.txt directly on Windows.

    Run once after cloning. Re-run after pulling dependency changes.

.PARAMETER Python
    Path to the python executable (default: python).
    For a specific version: -Python "C:\Python311\python.exe"

.PARAMETER RequirementsFile
    Requirements file to install (default: requirements-windows.txt).

.PARAMETER WithBeamNG
    Also installs beamngpy (requires BeamNG.tech licence).

.PARAMETER SkipVerify
    Skip running verify_env.py after installation.

.EXAMPLE
    .\setup_windows.ps1
    .\setup_windows.ps1 -Python "py -3.11"
    .\setup_windows.ps1 -WithBeamNG
    .\setup_windows.ps1 -SkipVerify
#>

param(
    [string]$Python = "python",
    [string]$RequirementsFile = "requirements-windows.txt",
    [switch]$WithBeamNG,
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
Write-Host "  Recommended: Python 3.11" -ForegroundColor White
Write-Host "  Requirements: requirements-windows.txt" -ForegroundColor White
Write-Host "  Primary simulator: BeamNG.tech (set BEAMNG_HOME after setup)" -ForegroundColor White
Write-Host ""

# 1. Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
try {
    $pyVer = & $Python --version 2>&1
    Write-Host "      Found: $pyVer" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: '$Python' not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Python 3.11 from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  - Check 'Add Python to PATH' during install." -ForegroundColor Yellow
    Write-Host "  - Or specify the path: .\setup_windows.ps1 -Python 'C:\Python311\python.exe'" -ForegroundColor Yellow
    exit 1
}

# Enforce minimum version
$verString = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$major, $minor = $verString.Split('.')
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 9)) {
    Write-Host "ERROR: Python 3.9+ required (found $verString)." -ForegroundColor Red
    Write-Host "       Python 3.11 is recommended." -ForegroundColor Yellow
    exit 1
}

if ([int]$major -eq 3 -and [int]$minor -ge 12) {
    Write-Host "      NOTE: Python $verString detected. 3.11 is recommended for best" -ForegroundColor Yellow
    Write-Host "      compatibility with TensorFlow on Windows." -ForegroundColor Yellow
}

# 2. Create / reuse virtual environment
Write-Host "[2/5] Setting up virtual environment (.venv)..." -ForegroundColor Yellow
$VenvDir = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "      Creating .venv with $Python..." -ForegroundColor White
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "      .venv created." -ForegroundColor Green
} else {
    Write-Host "      .venv already exists - reusing." -ForegroundColor Green
}

$Activate = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $Activate)) {
    Write-Host "ERROR: Activation script not found: $Activate" -ForegroundColor Red
    exit 1
}
. $Activate
Write-Host "      Activated." -ForegroundColor Green

# 3. Upgrade pip tooling
Write-Host "[3/5] Upgrading pip, setuptools, wheel..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "      WARNING: pip upgrade had errors - continuing." -ForegroundColor Yellow
}
Write-Host "      Done." -ForegroundColor Green

# 4. Install requirements
Write-Host "[4/5] Installing from $RequirementsFile..." -ForegroundColor Yellow

if (-not (Test-Path $RequirementsFile)) {
    Write-Host "      WARNING: $RequirementsFile not found." -ForegroundColor Yellow
    if (Test-Path "requirements.txt") {
        Write-Host "      Falling back to requirements.txt (WARNING: 'carla' will fail)." -ForegroundColor Yellow
        $RequirementsFile = "requirements.txt"
    } else {
        Write-Host "ERROR: No requirements file found." -ForegroundColor Red
        exit 1
    }
}

python -m pip install -r $RequirementsFile
$installResult = $LASTEXITCODE

if ($installResult -ne 0) {
    Write-Host ""
    Write-Host "Some packages failed. Retrying failed packages individually..." -ForegroundColor Yellow

    $failed = @()
    Get-Content $RequirementsFile | Where-Object {
        $_.Trim() -ne '' -and -not $_.TrimStart().StartsWith('#')
    } | ForEach-Object {
        $pkg = $_.Trim()
        python -m pip install $pkg --quiet 2>$null
        if ($LASTEXITCODE -ne 0) { $failed += $pkg }
    }

    if ($failed.Count -gt 0) {
        Write-Host ""
        Write-Host "  Packages that could NOT be installed automatically:" -ForegroundColor Red
        $failed | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
        Write-Host ""
        Write-Host "  This is expected for 'carla' and 'beamngpy'." -ForegroundColor Yellow
        Write-Host "  See docs\WINDOWS_SETUP.md for manual install steps." -ForegroundColor Yellow
    }
} else {
    Write-Host "      All packages installed." -ForegroundColor Green
}

# Optional: beamngpy
if ($WithBeamNG) {
    Write-Host ""
    Write-Host "[4b] Installing beamngpy (BeamNG.tech Python client)..." -ForegroundColor Yellow
    python -m pip install beamngpy
    if ($LASTEXITCODE -eq 0) {
        Write-Host "     beamngpy installed." -ForegroundColor Green
        Write-Host "     Set BEAMNG_HOME to your BeamNG install path before running." -ForegroundColor White
    } else {
        Write-Host "     beamngpy install failed. Check https://pypi.org/project/beamngpy/" -ForegroundColor Red
    }
}

# 5. Verify
if (-not $SkipVerify) {
    Write-Host "[5/5] Running environment verification..." -ForegroundColor Yellow
    python verify_env.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  Some checks FAILED (see output above)." -ForegroundColor Red
        Write-Host "  Fix the issues and re-run setup_windows.ps1 or verify_env.py." -ForegroundColor Yellow
    }
} else {
    Write-Host "[5/5] Skipping verification (-SkipVerify)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  .\run_windows.ps1                  # start CV lane detection (always works)" -ForegroundColor White
Write-Host "  .\run_windows.ps1 -Mode all-services  # start all 6 services" -ForegroundColor White
Write-Host "  .\diagnose_windows.ps1             # full diagnostics" -ForegroundColor White
Write-Host ""
Write-Host "For BeamNG simulation:" -ForegroundColor Yellow
Write-Host "  `$env:BEAMNG_HOME = 'C:\Path\To\BeamNG.tech.vX.X'" -ForegroundColor Cyan
Write-Host "  .\run_windows.ps1 -Mode beamng" -ForegroundColor Cyan
Write-Host ""
