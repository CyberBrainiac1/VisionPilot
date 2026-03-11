# VisionPilot - Windows Codebase Status

> Internal developer note. Updated: March 2026.

---

## Decisions Made

| Decision | Choice | Why |
|----------|--------|-----|
| Primary simulator | **BeamNG.tech** | `simulation/beamng.py` is complete. No `run_carla.py` exists. |
| Python version | **3.11** (min 3.9) | Best Windows wheel coverage for TF 2.19 + PyTorch + OpenCV. |
| Default entry point | **CV lane detection only** | Only service that works without model weights. Guaranteed first-run success. |
| Dependency file | **`requirements-windows.txt`** | Removes `carla` (not on PyPI); pins `numpy<2.0` (required by TF). |
| BeamNG home config | **`BEAMNG_HOME` env var wins over YAML** | YAML had hardcoded user path. Env var is portable. |
| CARLA references | **Removed from default scripts** | No `simulation/run_carla.py` exists. CARLA is future work. |
| README CARLA notice | **Removed** | Stale notice said "transitioning to CARLA" — contradicts BeamNG-first decision. |
| `config/config.py` BEAMNG_HOME | **Reads `BEAMNG_HOME` env var first** | Hardcoded dev path replaced with `os.environ.get()` fallback pattern. |
| Test import path | **`src.communication.aggregator`** | `tests/test_aggregator.py` had wrong `sys.path` and bare `from aggregator import`. |

### Alternatives Rejected

- **CARLA as primary simulator**: No `simulation/run_carla.py` exists. Zero runnable CARLA code. Would be misleading.
- **`requirements.txt` for Windows**: Contains `carla` which is not on PyPI. Always fails `pip install -r requirements.txt`.
- **Python 3.12 as default**: Works, but TF 2.19 wheels are less reliable. 3.11 is the safe choice.
- **Starting all 6 services by default**: 5 of 6 need model files. A default that requires manual model downloads is not a successful first run.

---

## Architecture Overview

```
project root/
  config/             YAML config (BeamNG, sensors, control, perception, scenarios)
  services/           Flask microservices (one per perception task)
    cv_lane_detection_service.py    port 4777  CV-only, no model needed  [ALWAYS-ON]
    object_detection_service.py     port 5777  YOLOv11, needs .pt
    traffic_light_detection_service.py port 6777  YOLOv11, needs .pt
    sign_detection_service.py       port 7777  YOLOv11, needs .pt
    sign_classification_service.py  port 8777  CNN, needs .h5
    yolop_service.py                port 9777  YOLOP, needs .pt + repo
  src/
    communication/aggregator/  Concurrent HTTP orchestrator
    perception/                Inference logic used by services
    sensor_fusion/             GPS, IMU, LiDAR, radar processors
    control_planning/          PID, PIDF, ACC, AEB, path planning
    mapping/                   SLAM stubs (not yet runnable)
  simulation/
    beamng.py                  Main simulation loop (requires BeamNG.tech)
    perception_client.py       Aggregator wrapper for BeamNG loop
  docker/                      Docker Compose + per-service Dockerfiles
  scripts/                     Launch helpers (bash + PowerShell)
  tests/                       Unit + integration tests
```

---

## What Works Right Now (Zero External Software)

| Component | Status | Notes |
|-----------|--------|-------|
| `verify_env.py` | OK | Full environment checker |
| `setup_windows.ps1` | OK | Creates venv, installs deps, verifies |
| `run_windows.ps1` (default) | OK | Starts CV lane detection (port 4777) |
| `diagnose_windows.ps1` | OK | Diagnostics report |
| `services/cv_lane_detection_service.py` | OK | No model needed |
| `src/communication/aggregator/` | OK | Fixed circular import |
| All `config/*.yaml` | OK | Load cleanly |

---

## What Requires Model Weights

All YOLO/CNN services need `.pt`/`.h5` files in `models/`. The files are not
distributed with the repo. Place them as:

```
models/
  object_detection/object_detection.pt
  traffic_light/traffic_light_detection.pt
  traffic_sign/traffic_sign_detection.pt
  traffic_sign/traffic_sign_classification.h5
  yolop/yolop.pt
```

---

## What Requires External Software

| Feature | Requires | Notes |
|---------|----------|-------|
| BeamNG simulation | BeamNG.tech licence + install | Set `BEAMNG_HOME` |
| `beamngpy` package | BeamNG.tech | `pip install beamngpy` |
| CARLA simulation | CARLA 0.9.x + `run_carla.py` | Not yet implemented |
| YOLOP inference | YOLOP repo at `/app/yolop_repo` | Docker or manual clone |
| Foxglove viz | `pip install foxglove-sdk` + Foxglove Studio | Optional — simulation runs without it |

---

## Bugs Fixed

| File | Bug | Fix |
|------|-----|-----|
| `config/__innit__.py` | Filename typo - prevented import | Renamed to `__init__.py` |
| `config/config.py` | Hardcoded `BEAMNG_HOME` path — broken on any machine except dev | Made `BEAMNG_HOME` read from env var with hardcoded path as fallback |
| `src/communication/aggregator/__init__.py` | Circular import | Changed to relative import `.aggregator` |
| `src/communication/aggregator/aggregator.py` | Sent frame as JSON list; services expected base64 | Changed to `base64.b64encode` |
| `src/communication/aggregator/aggregator.py` | ThreadPoolExecutor crash with 0 services | Added `max(len, 1)` guard |
| `services/cv_lane_detection_service.py` | Missing `return response, 200` | Added return; switched to base64 decode |
| `services/sign_classification_service.py` | Expected list, not base64 | Switched to base64 decode |
| `simulation/beamng.py` | Loaded config from wrong dir | Fixed to `../config` |
| `simulation/beamng.py` | Ignored `BEAMNG_HOME` env var | Added env var override logic |
| `simulation/beamng.py` | Top-level `import tensorflow`, `import torch`, `from ultralytics import YOLO` — crashes if packages absent, not used in this file | Removed unused imports |
| `simulation/beamng.py` | `from foxglove.schemas import Color` crashes if foxglove not installed | Wrapped in `try/except ImportError` |
| `simulation/beamng.py` | `radar_name.poll()` in sensor test loop — `radar_name` is a string key, not a Radar object | Fixed to `radar.poll()` |
| `simulation/beamng.py` | Dead throttle computation before speed-mode block was immediately overwritten by `throttle = 0.0` | Removed dead lines |
| `simulation/beamng.py` | Foxglove bridge used before `start_server()` + `initialize_channels()` were called | Added bridge startup at start of `main()` with `if bridge is not None:` guard |
| `simulation/beamng.py` | `car_pos` and `direction` can be `None` briefly at startup; arithmetic on `None` crashes | Added early-continue guard; `car_pos_arr = np.array(car_pos)` for safe arithmetic |
| `simulation/beamng.py` | `bridge.lane_channel.log(...)` called without null-check on `bridge` | Wrapped with `if bridge is not None:` |
| `simulation/beamng.py` | `car_pos + np.array([...])` fails when `car_pos` is a list/tuple | Changed to `car_pos_arr + np.array([...])` |
| `simulation/perception_client.py` | `from aggregator import PerceptionAggregator` — wrong module path | Fixed to `from src.communication.aggregator import PerceptionAggregator, AggregationResult` |
| `simulation/foxglove_integration/bridge_instance.py` | No guard — crashes at import if `foxglove` not installed | Wrapped in `try/except ImportError`; `bridge = None` fallback |
| `simulation/foxglove_integration/foxglove_bridge.py` | `_get_urdf_path()` used `"model"` directory name; actual dir is `"3d_model"` | Fixed to `"3d_model"` |
| `simulation/foxglove_integration/foxglove_bridge.py` | 5 GLB mesh paths hardcoded as absolute Windows dev-machine paths | Replaced with `Path(__file__).parent / "3d_model" / "bmw_x5" / "meshes"` relative paths |
| `scripts/start_simulation.ps1` | Hardcoded CARLA path + missing file | Rewritten for BeamNG + `BEAMNG_HOME` |
| `tests/aeb/test_aeb.py` | Loaded config from `beamng_sim/config/` (old path) | Fixed to `../../config/` |
| `tests/test_aggregator.py` | `sys.path` pointed to `tests/` not project root; bare `from aggregator import` | Set `project_root` to `Path(__file__).parent.parent`; import from `src.communication.aggregator` |
| `src/perception/object_detection/object_detection.py` | Hard `import tensorflow` broke service | Made optional |
| `src/perception/sign_detection/detect_classify.py` | Hard `import tensorflow` broke service | Made optional |
| Multiple `src/` dirs | Missing `__init__.py` blocked imports | Created empty `__init__.py` files |
| `README.md` | Stale "transitioning to CARLA" notice contradicted BeamNG-first decision | Removed the notice |

---

## Remaining Stale Code

- `src/mapping/` - SLAM stubs, not runnable
- CARLA: only references, no implementation
- `simulation/drive_log/data.py` - no active consumer
- `tests/object_detection/test_obj_det.py` - not verified
