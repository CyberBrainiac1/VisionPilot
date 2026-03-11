# VisionPilot — BeamNG Quick-Start

> **Audience:** You already own a BeamNG.tech licence and have it installed.

---

## Prerequisites

Install these first (each is a one-click installer):

| Tool | Version | Download |
|------|---------|----------|
| Python | **3.11** | [python.org/downloads](https://www.python.org/downloads/) — check **"Add Python to PATH"** |
| Git | any | [git-scm.com](https://git-scm.com/) |
| BeamNG.tech | 0.37+ | Already installed ✓ |

---

## First-time setup

Open **PowerShell** and run these two blocks. That's all you need to copy.

**Block 1 — Unlock PowerShell scripts** *(one-time, ever)*

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Block 2 — Clone, install, and launch** *(edit the path to match your BeamNG install)*

```powershell
git clone https://github.com/CyberBrainiac1/VisionPilot.git
cd VisionPilot
.\quickstart_beamng.ps1 -BeamNGHome "C:\Users\YourName\BeamNG.tech.v0.37.6.0"
```

> **Only edit** `C:\Users\YourName\BeamNG.tech.v0.37.6.0` — replace it with the actual
> folder that contains `BeamNG.tech.exe`.

The script will:
1. Verify BeamNG is at that path.
2. Create a Python virtual environment and install all dependencies (including `beamngpy`).
3. Save `BEAMNG_HOME` to your user environment so future terminals inherit it automatically.
4. Start all perception services and launch the BeamNG simulation loop.

---

## Every run after that

```powershell
cd VisionPilot
.\run_windows.ps1 -Mode beamng
```

---

## What gets started

| Service | Port | Notes |
|---------|------|-------|
| CV lane detection | 4777 | Always on, no model file needed |
| Object detection | 5777 | Needs `models\object_detection\object_detection.pt` |
| Traffic light detection | 6777 | Needs `models\traffic_light\traffic_light_detection.pt` |
| Sign detection | 7777 | Needs `models\traffic_sign\traffic_sign_detection.pt` |
| Sign classification | 8777 | Needs `models\traffic_sign\traffic_sign_classification.h5` |
| YOLOP | 9777 | Needs `models\yolop\yolop.pt` |
| BeamNG simulation loop | — | `simulation\beamng.py` |

Services without model files start but return errors at inference time.
See [WINDOWS_SETUP.md](WINDOWS_SETUP.md#model-weights) for where to place the weight files.

---

## Optional: real-time visualisation (Foxglove)

```powershell
.\.venv\Scripts\Activate.ps1
pip install foxglove-sdk
```

Then open [Foxglove Studio](https://foxglove.dev/studio) and connect to `ws://localhost:8765`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `cannot be loaded because running scripts is disabled` | Run Block 1 above |
| `BeamNG.tech not found` | Check the path — it must contain `BeamNG.tech.exe` |
| `.venv not found` | `.\setup_windows.ps1 -WithBeamNG` |
| `BEAMNG_HOME not set` in a new terminal | Re-run Block 2 once; the env var is then persisted |
| Services show `[!!]` | Missing model weight files — check `logs\<service>.err` |
| Port conflict | `Get-Process python \| Stop-Process` |
| Anything else | `.\diagnose_windows.ps1` |
