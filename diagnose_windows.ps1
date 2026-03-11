<#
.SYNOPSIS
    VisionPilot diagnostics script for Windows.

.DESCRIPTION
    Collects environment info, tests imports, checks config,
    probes ports, and prints a readable diagnostic report.
    Use this when something is not working.

.EXAMPLE
    .\diagnose_windows.ps1
#>

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Write-Section($title) {
    Write-Host ""
    Write-Host "── $title" -ForegroundColor Cyan
    Write-Host ("─" * 55) -ForegroundColor DarkCyan
}

function Write-OK($msg)   { Write-Host "  [OK]  $msg" -ForegroundColor Green  }
function Write-Warn($msg) { Write-Host "  [!!]  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  [XX]  $msg" -ForegroundColor Red    }

# ── Header ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  VisionPilot Diagnostics Report" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# ── System info ───────────────────────────────────────────────────────────────
Write-Section "System Information"
Write-Host "  OS          : $([System.Environment]::OSVersion.VersionString)"
Write-Host "  Machine     : $env:COMPUTERNAME"
Write-Host "  Username    : $env:USERNAME"
Write-Host "  Project dir : $ProjectRoot"
Write-Host "  PowerShell  : $($PSVersionTable.PSVersion)"

# ── Python check ─────────────────────────────────────────────────────────────
Write-Section "Python"
$PythonExe = "python"
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
    Write-OK ".venv activated"
    $PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
} else {
    Write-Warn ".venv not found – using system Python"
}

try {
    $pyVer = & $PythonExe --version 2>&1
    Write-OK "Python: $pyVer"
} catch {
    Write-Fail "Python not found on PATH"
}

# ── Packages ─────────────────────────────────────────────────────────────────
Write-Section "Key Package Versions"
$pkgs = @("numpy","opencv-python","flask","requests","ultralytics","tensorflow","torch","beamngpy","carla")
foreach ($pkg in $pkgs) {
    $ver = & $PythonExe -c "import importlib.metadata; print(importlib.metadata.version('$pkg'))" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-OK "$pkg $ver"
    } else {
        Write-Warn "$pkg – not installed"
    }
}

# ── Config files ─────────────────────────────────────────────────────────────
Write-Section "Config Files"
$configs = @(
    "config\beamng_sim.yaml",
    "config\control.yaml",
    "config\perception.yaml",
    "config\scenarios.yaml",
    "config\sensors.yaml"
)
foreach ($cfg in $configs) {
    if (Test-Path $cfg) {
        Write-OK $cfg
    } else {
        Write-Fail "$cfg – MISSING"
    }
}

# ── Model files ───────────────────────────────────────────────────────────────
Write-Section "Model Files"
$models = @(
    "models\object_detection\object_detection.pt",
    "models\traffic_light\traffic_light_detection.pt",
    "models\traffic_sign\traffic_sign_detection.pt",
    "models\traffic_sign\traffic_sign_classification.h5",
    "models\yolop\yolop.pt"
)
foreach ($m in $models) {
    if (Test-Path $m) {
        $size = (Get-Item $m).Length / 1MB
        Write-OK "$m  ($([math]::Round($size,1)) MB)"
    } else {
        Write-Warn "$m – not present (service will fail at inference)"
    }
}

# ── Environment variables ─────────────────────────────────────────────────────
Write-Section "Environment Variables"
$vars = @("BEAMNG_HOME","MODEL_PATH","PYTHONPATH","CUDA_VISIBLE_DEVICES")
foreach ($v in $vars) {
    $val = [System.Environment]::GetEnvironmentVariable($v)
    if ($val) {
        Write-OK "$v = $val"
    } else {
        Write-Warn "$v – not set"
    }
}

# ── BeamNG home ───────────────────────────────────────────────────────────────
Write-Section "BeamNG.tech"
$bnHome = $env:BEAMNG_HOME
if ($bnHome -and (Test-Path $bnHome)) {
    Write-OK "Found at: $bnHome"
} elseif ($bnHome) {
    Write-Fail "BEAMNG_HOME set but path not found: $bnHome"
} else {
    Write-Warn "BEAMNG_HOME not set – BeamNG simulation unavailable"
    Write-Host "           Set with: `$env:BEAMNG_HOME = 'C:\Path\To\BeamNG.tech.vX.X'" -ForegroundColor DarkYellow
}

# ── Port probe ────────────────────────────────────────────────────────────────
Write-Section "Service Ports (health check)"
$services = @(
    @{Name="cv_lane_detection";       Port=4777},
    @{Name="object_detection";        Port=5777},
    @{Name="traffic_light_detection"; Port=6777},
    @{Name="sign_detection";          Port=7777},
    @{Name="sign_classification";     Port=8777},
    @{Name="yolop";                   Port=9777}
)

foreach ($svc in $services) {
    $url = "http://localhost:$($svc.Port)/health"
    try {
        $resp = Invoke-RestMethod -Uri $url -TimeoutSec 2 -ErrorAction Stop
        Write-OK "$($svc.Name)  port $($svc.Port)  RUNNING"
    } catch {
        Write-Warn "$($svc.Name)  port $($svc.Port)  not responding (service not started)"
    }
}

# ── Internal import test ──────────────────────────────────────────────────────
Write-Section "Internal Module Imports"
$mods = @(
    @{Mod="config.config";                     Desc="config.config"},
    @{Mod="src.communication.aggregator";      Desc="aggregator package"},
    @{Mod="src.perception.lane_detection.main";Desc="CV lane detection"},
    @{Mod="src.perception.object_detection.main"; Desc="object detection"}
)

foreach ($item in $mods) {
    $result = & $PythonExe -c "
import sys
sys.path.insert(0,'$($ProjectRoot.Replace('\','/'))')
try:
    import $($item.Mod)
    print('OK')
except ImportError as e:
    print(f'FAIL: {e}')
except Exception as e:
    print(f'WARN: {e}')
" 2>&1

    if ($result -like "OK*") {
        Write-OK $item.Desc
    } elseif ($result -like "WARN*") {
        Write-Warn "$($item.Desc) – $result"
    } else {
        Write-Fail "$($item.Desc) – $result"
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Diagnostics complete." -ForegroundColor Green
Write-Host "  Review [!!] and [XX] items above." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Useful next steps:" -ForegroundColor White
Write-Host "    .\setup_windows.ps1     – install / repair environment" -ForegroundColor White
Write-Host "    python verify_env.py    – detailed Python-level checks" -ForegroundColor White
Write-Host "    .\run_windows.ps1       – launch the service stack" -ForegroundColor White
Write-Host "    docs\WINDOWS_SETUP.md  – full setup guide" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
