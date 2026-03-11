# VisionPilot - Windows Run Guide

## Shortest Path to First Successful Run

```powershell
# 1. Allow PowerShell scripts (one-time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. Clone and enter
git clone https://github.com/CyberBrainiac1/VisionPilot.git
cd VisionPilot

# 3. Setup (creates .venv, installs deps, verifies)
.\setup_windows.ps1

# 4. Start CV lane detection (guaranteed working, no model files needed)
.\run_windows.ps1
```

### Expected output

```
==========================================
  VisionPilot - Windows Launcher
  Mode: services
==========================================

[VisionPilot] Virtual environment activated
[VisionPilot] Checking environment...
  [OK]  Python 3.11.x (recommended)
  [OK]  numpy
  ...
  All critical checks passed.

[VisionPilot] Starting services...

  cv_lane_detection  :4777  OpenCV lane detection - no model file required  [PID 1234]

[VisionPilot] Waiting for services to initialise...

Health check:

  [OK]  cv_lane_detection   http://localhost:4777

CV lane detection is live at http://localhost:4777

  GET  http://localhost:4777/health   -- health check
  POST http://localhost:4777/process  -- process a frame

To start all 6 services: .\run_windows.ps1 -Mode all-services

Press Enter to stop.
```

---

## Command Reference

| Command | What it does |
|---------|--------------|
| `.\run_windows.ps1` | Start CV lane detection only (always works) |
| `.\run_windows.ps1 -Mode all-services` | Start all 6 services (needs model files for most) |
| `.\run_windows.ps1 -Mode beamng` | Start all services + BeamNG simulation |
| `.\run_windows.ps1 -Mode verify` | Environment check only, nothing started |
| `.\run_windows.ps1 -SkipVerify` | Skip env check at startup |
| `.\setup_windows.ps1` | Create/repair .venv, install deps |
| `.\setup_windows.ps1 -WithBeamNG` | Also installs beamngpy |
| `.\diagnose_windows.ps1` | Full diagnostics report |
| `python verify_env.py` | Python-level environment checks |
| `.\scripts\start_services.ps1` | Start all services directly (no launcher) |
| `.\scripts\start_simulation.ps1` | BeamNG simulation (needs BEAMNG_HOME) |

---

## Running with All Services

Requires model weight files in `models/`. Services without weights exit immediately.

```powershell
.\run_windows.ps1 -Mode all-services
```

Output with no model files:

```
Model file status:
  [!!] object_detection - model not found, service exits at startup
  [!!] traffic_light_detection - model not found, service exits at startup
  ...

Health check:
  [OK]  cv_lane_detection   http://localhost:4777
  [!!]  object_detection    http://localhost:5777  - not responding
  ...
```

---

## Running with BeamNG

Requirements: BeamNG.tech licence, BeamNG installed.

```powershell
# Set your BeamNG install path
$env:BEAMNG_HOME = "C:\Users\<you>\BeamNG.tech.v0.37.6.0"

# Start all services + BeamNG simulation loop
.\run_windows.ps1 -Mode beamng
```

The `BEAMNG_HOME` env var always takes priority over `config/beamng_sim.yaml`.

---

## Running Individual Services

```powershell
.\.venv\Scripts\Activate.ps1

# CV lane detection (no model needed)
python services\cv_lane_detection_service.py

# Object detection (needs .pt)
$env:MODEL_PATH = "models\object_detection\object_detection.pt"
python services\object_detection_service.py
```

Test with curl or PowerShell:

```powershell
# Health check
Invoke-RestMethod http://localhost:4777/health

# Send a frame (from file)
$img = [Convert]::ToBase64String([IO.File]::ReadAllBytes("path\to\image.jpg"))
$body = @{ frame = $img; frame_shape = @(1080, 1920, 3) } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri http://localhost:4777/process `
    -Body $body -ContentType "application/json"
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Script blocked | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `.venv not found` | `.\setup_windows.ps1` |
| `carla` install fails | Use `requirements-windows.txt` (the default) |
| Service shows `[!!]` | Missing model `.pt`/`.h5` in `models/` - check `logs\<name>.err` |
| Port already in use | `Get-Process python \| Stop-Process` |
| `BEAMNG_HOME` not recognized | `$env:BEAMNG_HOME = "C:\Path\To\BeamNG"` |
| All services fail to start | `python verify_env.py` then `.\diagnose_windows.ps1` |

---

## Logs

```
logs\
  cv_lane_detection.log    stdout
  cv_lane_detection.err    stderr  <- check this on failure
  object_detection.log
  object_detection.err
  ...
```

---

## Architecture

```
run_windows.ps1  (default: Mode=services)
      |
      +-- always-on: cv_lane_detection (4777)
      |
      +-- needs-model: object_detection (5777)
      |                traffic_light (6777)
      |                sign_detection (7777)
      |                sign_classification (8777)
      |                yolop (9777)
      |
      +-- beamng mode: simulation\beamng.py
              |
              +-- PerceptionAggregator (HTTP, base64 frames)
                      |
                      +-> POST /process to all services concurrently
```
