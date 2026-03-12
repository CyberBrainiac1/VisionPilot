# VisionPilot - Windows Setup Guide

## Decisions

- **Python 3.11** is the standard. It has the best Windows wheel coverage for TF 2.19 + PyTorch + OpenCV.
- **`requirements-windows.txt`** is the only file you need. It removes `carla` (not on PyPI) and pins `numpy<2.0`.
- **BeamNG.tech** is the primary simulator. CARLA is not yet implemented (`simulation/run_carla.py` does not exist).
- **Default entry point**: CV lane detection service (port 4777). It works without any model files on a clean install.

---

## Prerequisites

| Requirement | Version | Get it |
|-------------|---------|--------|
| Python | **3.11** (3.9-3.12 accepted) | [python.org/downloads](https://www.python.org/downloads/) - check "Add to PATH" |
| Git | any | [git-scm.com](https://git-scm.com/) |
| PowerShell | 5.1+ (PS 7 recommended) | Built-in on Windows 10/11 |

Optional:
| Requirement | Version | Notes |
|-------------|---------|-------|
| CUDA | 11.x or 12.x | For GPU acceleration (services default to CPU) |
| Docker Desktop | 4.x | For containerised services |
| BeamNG.tech | 0.37+ | Requires paid licence |
| CARLA | 0.9.16 | Not yet integrated |

> **First-time PowerShell setup:**
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

## Quick Setup

```powershell
git clone https://github.com/CyberBrainiac1/VisionPilot.git
cd VisionPilot
.\setup_windows.ps1
```

Done. Run `.\run_windows.ps1` to start the CV lane detection service.

---

## What setup_windows.ps1 Does

1. Checks Python >= 3.9 (recommends 3.11)
2. Creates `.venv` (skips if exists)
3. Upgrades `pip`, `setuptools`, `wheel`
4. Installs `requirements-windows.txt`
5. Runs `verify_env.py`

### With BeamNG support

```powershell
.\setup_windows.ps1 -WithBeamNG
```

This additionally runs `pip install beamngpy`.

---

## Why requirements-windows.txt Exists

`requirements.txt` includes `carla` which is not on PyPI - `pip install -r requirements.txt` always fails on Windows.

`requirements-windows.txt` fixes this:
- Removes `carla` entirely (CARLA integration not yet implemented)
- Removes `beamngpy` (install separately only with a BeamNG licence)
- Pins `numpy>=1.22.4,<2.0` (numpy 2.x breaks TensorFlow 2.19)
- Adds explicit `pyyaml` and `scipy` which `requirements.txt` omitted

---

## Optional: Foxglove Visualization

Foxglove Studio provides real-time 3D visualization of the simulation (LiDAR point cloud, vehicle pose, lane detections, camera feed, 2D/3D bounding boxes).

The simulation runs without it — all `bridge.*` calls silently no-op if foxglove is not installed.

```powershell
pip install foxglove-sdk
```

Then open [Foxglove Studio](https://foxglove.dev/studio) and connect to `ws://localhost:8765`.

---

## Optional: BeamNG.tech

1. Purchase a [BeamNG.tech](https://www.beamng.tech/) licence.
2. Install (e.g. `C:\Users\<you>\BeamNG.tech.v0.37.6.0`).
3. Install the Python client:
   ```powershell
   pip install beamngpy
   # or during setup:
   .\setup_windows.ps1 -WithBeamNG
   ```
4. Set the environment variable:
   ```powershell
   $env:BEAMNG_HOME = "C:\Users\<you>\BeamNG.tech.v0.37.6.0"
   ```
5. Start:
   ```powershell
   .\run_windows.ps1 -Mode beamng
   ```

The `BEAMNG_HOME` environment variable always overrides the path in `config/beamng_sim.yaml`.

---

## Optional: CARLA

> **Status: not yet implemented.** `simulation/run_carla.py` does not exist.

CARLA integration is future work. If you want to prepare:

1. Download CARLA 0.9.16 from [GitHub releases](https://github.com/carla-simulator/carla/releases).
2. Install the client wheel:
   ```powershell
   pip install "C:\CARLA_0.9.16\PythonAPI\carla\dist\carla-0.9.16-cp311-win_amd64.whl"
   ```
3. Wait for `simulation/run_carla.py` to be implemented.

---

## Model Weights

Model weights are not distributed with the repo. Place them in:

```
models/
  object_detection/object_detection.pt          (YOLOv11 - object detection)
  traffic_light/traffic_light_detection.pt       (YOLOv11 - traffic lights)
  traffic_sign/traffic_sign_detection.pt         (YOLOv11 - sign detection)
  traffic_sign/traffic_sign_classification.h5    (CNN - sign classification)
  yolop/yolop.pt                                 (YOLOP - unified perception)
```

Services that need model weights (`MODEL_PATH` env var) exit immediately at startup
if the weight file is not present. CV lane detection (port 4777) needs no model file
and always starts cleanly.

---

## Common Issues

### `carla` install fails
**Fix:** Use `requirements-windows.txt` (the default). Never use `requirements.txt` directly on Windows.

### `beamngpy` not found
**Fix:** `pip install beamngpy` - only needed for simulation, not for services.

### PowerShell execution policy error
**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `tensorflow` is slow to install / fails on 3.12
TF 2.19 supports 3.9-3.12 but Python 3.11 has the most stable wheels.
```powershell
pip install tensorflow==2.19.0
```

### OpenCV `DLL load failed` on Windows
```powershell
pip install opencv-python-headless   # more reliable on server/headless installs
```

### Services show `[!!]` in health check
Services that need model weights exit immediately at startup without the `.pt`/`.h5` files.
Check `logs\<service>.err` for details.
