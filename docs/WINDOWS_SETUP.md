# VisionPilot – Windows Setup Guide

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Windows 10/11 | 64-bit | |
| Python | 3.9 – 3.12 | [python.org](https://www.python.org/downloads/) – add to PATH |
| Git | any | [git-scm.com](https://git-scm.com/) |
| PowerShell | 5.1+ (or PS 7) | Windows built-in |
| CUDA (optional) | 11.x / 12.x | For GPU acceleration |
| Docker Desktop (optional) | 4.x | For containerised services |
| BeamNG.tech (optional) | 0.37+ | Requires licence |
| CARLA (optional) | 0.9.16 | Requires separate install |

> **PowerShell execution policy**  
> If scripts are blocked, run once as Administrator:  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

## Quick Setup

```powershell
# Clone the repo
git clone https://github.com/CyberBrainiac1/VisionPilot.git
cd VisionPilot

# One-shot setup (creates .venv, installs deps, verifies)
.\setup_windows.ps1
```

That's it for the base install. See sections below for simulator-specific steps.

---

## What `setup_windows.ps1` does

1. Verifies Python ≥ 3.9 is on `PATH`
2. Creates `.venv` virtual environment (skips if already exists)
3. Upgrades `pip`, `setuptools`, `wheel`
4. Installs `requirements-windows.txt`
5. Runs `verify_env.py` to confirm the installation

---

## Why `requirements-windows.txt` Exists

The default `requirements.txt` contains `carla`, which is **not available on
PyPI**. Running `pip install -r requirements.txt` will fail on Windows.

`requirements-windows.txt` removes `carla` and any other packages that need
manual installation on Windows. Install optional simulator packages separately
(see sections below).

---

## Optional: BeamNG.tech Integration

1. Purchase / obtain a [BeamNG.tech](https://www.beamng.tech/) licence.
2. Install BeamNG.tech (e.g. `C:\Users\<you>\BeamNG.tech.v0.37.6.0`).
3. Install the Python client:
   ```powershell
   pip install beamngpy
   ```
4. Set the environment variable (add to your PowerShell profile for persistence):
   ```powershell
   $env:BEAMNG_HOME = "C:\Users\<you>\BeamNG.tech.v0.37.6.0"
   ```
5. Start the simulation:
   ```powershell
   .\scripts\start_simulation.ps1
   # or
   .\run_windows.ps1 -Mode beamng
   ```

---

## Optional: CARLA Integration

> **Status:** CARLA integration is **in-progress**. The `simulation/run_carla.py`
> entrypoint does not yet exist.

1. Download CARLA 0.9.16 from the [CARLA releases page](https://github.com/carla-simulator/carla/releases).
2. Install the Python client wheel:
   ```powershell
   pip install "<CARLA_ROOT>\PythonAPI\carla\dist\carla-0.9.16-cp3x-win_amd64.whl"
   ```
3. Launch CARLA:
   ```powershell
   & "C:\CARLA_0.9.16\CarlaUE4.exe"
   ```
4. When `simulation/run_carla.py` is complete, run:
   ```powershell
   python simulation\run_carla.py
   ```

---

## Optional: Docker Services (recommended for production)

```powershell
# From the docker\ directory
cd docker
docker compose up -d

# Check health
.\scripts\start_services.sh    # bash/WSL
```

Docker services require GPU passthrough (`nvidia` driver) for full
performance. Without GPU they fall back to CPU.

---

## Model Weights

Model weights are **not distributed** with the repository (too large, proprietary
training data). Place them as follows:

```
models/
├── object_detection/
│   └── object_detection.pt
├── traffic_light/
│   └── traffic_light_detection.pt
├── traffic_sign/
│   ├── traffic_sign_detection.pt
│   └── traffic_sign_classification.h5
└── yolop/
    └── yolop.pt
```

Services will start without model files but return errors on inference
(`/process` endpoint). The CV lane detection service (port 4777) works
without any model files.

---

## Common Issues

### `carla` install fails
```
ERROR: Could not find a version that satisfies the requirement carla
```
**Fix:** `carla` is not on PyPI. Use `requirements-windows.txt` (the default)
or install the wheel from the CARLA release package.

### `beamngpy` import fails
```
ModuleNotFoundError: No module named 'beamngpy'
```
**Fix:** `pip install beamngpy` (only needed for simulation).

### PowerShell script blocked
```
.\setup_windows.ps1 : File ... cannot be loaded because running scripts is disabled
```
**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `tensorflow` install slow / fails on Python 3.12
TensorFlow 2.19 supports Python 3.9–3.12. If install fails try:
```powershell
pip install tensorflow==2.19.0 --no-binary :all:
```

### OpenCV `cv2` import error (DLL load failed on Windows)
```powershell
pip install opencv-python-headless   # headless version, more reliable on servers
```

### Services not responding on health check
- Check `logs\<service>.err` for startup errors.
- Services that require `MODEL_PATH` will exit immediately if the file does
  not exist.
- Run `python verify_env.py` for a full diagnosis.

---

## What Currently Works Without a Simulator

| Feature | Works standalone? |
|---------|-------------------|
| CV lane detection service (port 4777) | ✅ Yes |
| Object detection service (port 5777) | ✅ With model `.pt` |
| Traffic light service (port 6777) | ✅ With model `.pt` |
| Sign detection service (port 7777) | ✅ With model `.pt` |
| Sign classification service (port 8777) | ✅ With model `.h5` |
| YOLOP service (port 9777) | ✅ With model + YOLOP repo |
| Aggregator (HTTP orchestration) | ✅ Yes |
| Environment checks (`verify_env.py`) | ✅ Yes |
| Diagnostics (`diagnose_windows.ps1`) | ✅ Yes |
| BeamNG simulation loop | ❌ Needs BeamNG.tech |
| CARLA simulation loop | ❌ Not yet implemented |
| Foxglove visualisation | ❌ Needs Foxglove + BeamNG |
