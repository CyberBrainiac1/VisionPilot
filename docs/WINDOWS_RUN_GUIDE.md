# VisionPilot – Windows Run Guide

## Shortest Path to First Successful Run

```powershell
# 1. Clone
git clone https://github.com/CyberBrainiac1/VisionPilot.git
cd VisionPilot

# 2. Setup (one-time)
.\setup_windows.ps1

# 3. Start perception services
.\run_windows.ps1
```

Expected output:

```
==========================================
  VisionPilot – Windows Launcher
  Mode: services
==========================================

[VisionPilot] Virtual environment activated (.venv)
[VisionPilot] Running environment verification...
  [OK]  Python 3.11.x
  [OK]  numpy
  [OK]  opencv-python
  [OK]  flask
  ...

[VisionPilot] Starting perception microservices...

  Starting cv_lane_detection (port 4777)... PID 12345
  Starting object_detection (port 5777)... PID 12346
  ...

[VisionPilot] Waiting 5s for services to initialise...

[VisionPilot] Checking service health...

  [OK]  cv_lane_detection  http://localhost:4777
  [!!]  object_detection   http://localhost:5777 – not responding
  ...

Services are running in the background.
Press Enter to stop all services.
```

> **Note:** Services requiring model weights (object_detection, traffic_light,
> sign_detection, sign_classification, yolop) will show `[!!]` until the
> corresponding `.pt` / `.h5` files are placed in `models/`.
> CV lane detection (port 4777) is always healthy.

---

## Command Reference

| Command | Description |
|---------|-------------|
| `.\setup_windows.ps1` | Create .venv, install deps, verify |
| `.\run_windows.ps1` | Start services + health check |
| `.\run_windows.ps1 -Mode beamng` | Start services + BeamNG simulation |
| `.\run_windows.ps1 -Mode verify` | Environment check only |
| `.\run_windows.ps1 -SkipVerify` | Skip env check at startup |
| `.\scripts\start_services.ps1` | Start services only (no launcher overhead) |
| `.\diagnose_windows.ps1` | Full diagnostics report |
| `python verify_env.py` | Python-level checks |
| `.\scripts\start_simulation.ps1` | BeamNG simulation (needs `BEAMNG_HOME`) |

---

## Running Individual Services

Each service can be run independently for testing:

```powershell
# Activate venv first
.\.venv\Scripts\Activate.ps1

# CV lane detection (no model needed)
python services\cv_lane_detection_service.py

# Object detection (needs model)
$env:MODEL_PATH = "models\object_detection\object_detection.pt"
python services\object_detection_service.py
```

Test a service endpoint:
```powershell
# Health check
Invoke-RestMethod http://localhost:4777/health

# Process a frame (example with PowerShell)
$frame = [System.IO.File]::ReadAllBytes("path\to\image.jpg")
$b64 = [Convert]::ToBase64String($frame)
$body = @{ frame = $b64; frame_shape = @(1080, 1920, 3) } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri http://localhost:4777/process -Body $body -ContentType "application/json"
```

---

## BeamNG Simulation

Requirements: BeamNG.tech licence, BeamNG.tech installed.

```powershell
# Set BeamNG home
$env:BEAMNG_HOME = "C:\Users\<you>\BeamNG.tech.v0.37.6.0"

# Start services + simulation
.\run_windows.ps1 -Mode beamng

# or just the simulation (services must already be running)
.\scripts\start_simulation.ps1
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `setup_windows.ps1` blocked | Execution policy | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `carla` install fails | Not on PyPI | Use `requirements-windows.txt` (default) |
| Services fail with `MODEL_PATH` error | Missing model weights | Add `.pt`/`.h5` files to `models/` |
| `verify_env.py` fails on `config.config` | Config `__init__` missing | Fixed in this branch |
| `ModuleNotFoundError: No module named 'src'` | Missing `__init__.py` | Fixed in this branch |
| Aggregator sends to services, all return 500 | Frame encoding mismatch | Fixed in this branch (now base64) |
| `beamng.py` can't find YAML configs | Wrong config path | Fixed in this branch |
| Port already in use | Old service process | `Get-Process python | Stop-Process` |

---

## Logs

Service logs are written to `logs\`:

```
logs\
├── cv_lane_detection.log     stdout
├── cv_lane_detection.err     stderr
├── object_detection.log
├── object_detection.err
└── ...
```

---

## Architecture Diagram

```
[Windows PowerShell]
       │
       ├─ run_windows.ps1 / start_services.ps1
       │
       ▼
[Python Flask Services]
  cv_lane_detection    :4777
  object_detection     :5777
  traffic_light        :6777
  sign_detection       :7777
  sign_classification  :8777
  yolop                :9777
       │
       ▼
[PerceptionAggregator]  ←── called from BeamNG simulation loop
  (concurrent HTTP, base64 frames)
       │
       ▼
[simulation/beamng.py]  ←── requires BeamNG.tech + licence
```
