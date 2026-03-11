# VisionPilot – Windows Codebase Status

> Internal developer note. Last updated: March 2026.

---

## Summary

VisionPilot is a modular Python project for autonomous driving research.
It is in **active development** with its primary simulation backend being
**BeamNG.tech** (fully integrated) while CARLA integration is in-progress
(a placeholder `scripts/start_simulation.ps1` referenced a non-existent
`simulation/run_carla.py` – fixed in this PR).

---

## Architecture Overview

```
project root
├── config/           YAML configuration (BeamNG, sensors, control, perception, scenarios)
├── services/         Flask microservices (one per perception task)
│   ├── cv_lane_detection_service.py      port 4777 – CV-based lane detection (NO model needed)
│   ├── object_detection_service.py       port 5777 – YOLOv11 object detection
│   ├── traffic_light_detection_service.py port 6777 – YOLOv11 traffic light
│   ├── sign_detection_service.py         port 7777 – YOLOv11 sign detection
│   ├── sign_classification_service.py    port 8777 – CNN sign classification
│   └── yolop_service.py                  port 9777 – YOLOP unified perception
├── src/
│   ├── communication/aggregator/  Concurrent HTTP aggregator
│   ├── perception/                Inference logic used by services
│   ├── sensor_fusion/             GPS, IMU, LiDAR, radar processors
│   ├── control_planning/          PID, PIDF, ACC, AEB, path planning
│   └── mapping/                   SLAM stubs (not yet runnable)
├── simulation/
│   ├── beamng.py                  Main simulation loop (requires BeamNG.tech)
│   └── perception_client.py       Wrapper around aggregator for BeamNG loop
├── docker/                        Docker Compose + per-service Dockerfiles
├── scripts/                       Launch helpers (bash + PowerShell)
└── tests/                         Unit & integration tests
```

---

## What Currently Works (Without Simulators)

| Component | Status | Notes |
|-----------|--------|-------|
| `services/cv_lane_detection_service.py` | ✅ Fully runnable | No model weights needed |
| `services/object_detection_service.py` | ✅ Starts, needs `.pt` for inference | Set `MODEL_PATH` env var |
| `services/traffic_light_detection_service.py` | ✅ Starts, needs `.pt` | Set `MODEL_PATH` env var |
| `services/sign_detection_service.py` | ✅ Starts, needs `.pt` | Set `MODEL_PATH` env var |
| `services/sign_classification_service.py` | ✅ Starts, needs `.h5` | Set `MODEL_PATH` env var |
| `services/yolop_service.py` | ✅ Starts, needs YOLOP model | Requires YOLOP repo libs |
| `src/communication/aggregator/` | ✅ Importable | Fixed circular import |
| `config/*.yaml` | ✅ Load cleanly | Fixed path in `simulation/beamng.py` |
| `verify_env.py` | ✅ New | Full environment checker |
| `setup_windows.ps1` | ✅ New | One-shot Windows setup |
| `run_windows.ps1` | ✅ New | Launcher with health check |
| `diagnose_windows.ps1` | ✅ New | Diagnostics report |

---

## What Requires External Software

| Component | Requirement | Notes |
|-----------|-------------|-------|
| `simulation/beamng.py` | BeamNG.tech licence + install | Set `BEAMNG_HOME` env var |
| `beamngpy` package | BeamNG.tech | `pip install beamngpy` then configure |
| `carla` package | CARLA simulator 0.9.x | Install from release `.whl`, not PyPI |
| YOLOP inference | YOLOP repo cloned to `/app/yolop_repo` | Docker or manual clone |
| Foxglove WebSocket | `foxglove` package + Foxglove Studio | Optional visualisation |
| Model weights (`*.pt`, `*.h5`) | Training / download | Not distributed with repo |

---

## Bugs Fixed in This Update

| File | Bug | Fix |
|------|-----|-----|
| `config/__innit__.py` | Filename typo prevents import | Renamed to `config/__init__.py` |
| `src/communication/aggregator/__init__.py` | Circular import (imported from itself) | Changed to relative import `.aggregator` |
| `src/communication/aggregator/aggregator.py` | Sent frame as JSON list; services expected base64 | Changed to `base64.b64encode(frame.tobytes())` |
| `services/cv_lane_detection_service.py` | Missing `return response, 200`; got list instead of base64 | Added return; switched to base64 decode |
| `services/sign_classification_service.py` | Got list instead of base64 | Switched to base64 decode |
| `simulation/beamng.py` | Loaded config from `simulation/config/` (wrong dir) | Fixed path to `../config` |
| `scripts/start_simulation.ps1` | Hardcoded CARLA path; referenced non-existent file | Rewritten for BeamNG with `BEAMNG_HOME` |
| Multiple `src/` directories | Missing `__init__.py` files | Created empty `__init__.py` files |

---

## Half-Migrated / Stale Code

- `simulation/drive_log/data.py` – referenced but no drive_log service
- `src/mapping/` – SLAM stubs, not runnable
- CARLA integration – only stub scripts, no `simulation/run_carla.py`
- `tests/aeb/test_aeb.py` loads config from `beamng_sim/config/` (old path)

---

## Recommended Next Steps

1. Add `beamngpy` to `requirements-windows.txt` once confirmed working on Windows
2. Create `simulation/run_carla.py` or remove CARLA references
3. Add `tests/test_services.py` with pytest-based service tests
4. Document model download / training steps in README
5. Fix `tests/aeb/test_aeb.py` config path
