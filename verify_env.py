"""
verify_env.py - VisionPilot environment verification script

Run with:  python verify_env.py
or inside run_windows.ps1 automatically.
"""

import sys
import os
import importlib
import platform
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent

# ── colour helpers ────────────────────────────────────────────────────────────
def _ok(msg):  print(f"  [OK]  {msg}")
def _warn(msg): print(f"  [!!]  {msg}")
def _fail(msg): print(f"  [XX]  {msg}")

# ── checks ────────────────────────────────────────────────────────────────────

def check_python_version():
    print("\n── Python version ──────────────────────────────────────")
    ver = sys.version_info
    if ver >= (3, 9):
        _ok(f"Python {ver.major}.{ver.minor}.{ver.micro}")
    else:
        _fail(f"Python {ver.major}.{ver.minor}.{ver.micro} - need >= 3.9")
        return False
    return True


def check_platform():
    print("\n── Platform ─────────────────────────────────────────────")
    plat = platform.system()
    _ok(f"{plat} {platform.release()} ({platform.machine()})")
    if plat != "Windows":
        _warn("Not Windows - scripts are optimised for Windows/PowerShell")


def check_required_imports():
    print("\n── Required packages ────────────────────────────────────")
    required = [
        ("numpy",        "numpy"),
        ("cv2",          "opencv-python"),
        ("flask",        "flask"),
        ("requests",     "requests"),
        ("yaml",         "pyyaml"),
        ("ultralytics",  "ultralytics"),
        ("PIL",          "Pillow"),
        ("scipy",        "scipy"),
        ("sklearn",      "scikit-learn"),
        ("pandas",       "pandas"),
        ("tqdm",         "tqdm"),
    ]

    all_ok = True
    for mod, pkg in required:
        try:
            importlib.import_module(mod)
            _ok(f"{pkg}")
        except ImportError:
            _fail(f"{pkg}  →  pip install {pkg}")
            all_ok = False
    return all_ok


def check_optional_imports():
    print("\n── Optional / simulator packages ────────────────────────")
    optional = [
        ("tensorflow",  "tensorflow",  "Deep-learning models (sign, traffic-light classification)"),
        ("torch",       "torch",       "PyTorch (YOLOP service)"),
        ("beamngpy",    "beamngpy",    "BeamNG.tech simulation (requires licence)"),
        ("carla",       "carla",       "CARLA simulator (install from release wheel)"),
    ]

    for mod, pkg, desc in optional:
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", "unknown")
            _ok(f"{pkg} {ver}  - {desc}")
        except ImportError:
            _warn(f"{pkg} not installed  - {desc}")


def check_config_files():
    print("\n── Config files ─────────────────────────────────────────")
    configs = [
        "config/beamng_sim.yaml",
        "config/control.yaml",
        "config/perception.yaml",
        "config/scenarios.yaml",
        "config/sensors.yaml",
    ]
    all_ok = True
    for cfg in configs:
        p = PROJECT_ROOT / cfg
        if p.exists():
            _ok(cfg)
        else:
            _fail(f"{cfg}  - MISSING")
            all_ok = False
    return all_ok


def check_config_loads():
    print("\n── Config YAML load ─────────────────────────────────────")
    try:
        import yaml
    except ImportError:
        _warn("PyYAML not available - skipping config load check")
        return True

    configs = {
        "beamng_sim":  "config/beamng_sim.yaml",
        "control":     "config/control.yaml",
        "perception":  "config/perception.yaml",
        "scenarios":   "config/scenarios.yaml",
        "sensors":     "config/sensors.yaml",
    }
    all_ok = True
    for name, rel in configs.items():
        p = PROJECT_ROOT / rel
        try:
            with open(p) as f:
                yaml.safe_load(f)
            _ok(f"{rel}")
        except FileNotFoundError:
            _fail(f"{rel}  - file not found")
            all_ok = False
        except yaml.YAMLError as e:
            _fail(f"{rel}  - YAML parse error: {e}")
            all_ok = False
    return all_ok


def check_entrypoints():
    print("\n── Key entrypoints ──────────────────────────────────────")
    entrypoints = [
        "simulation/beamng.py",
        "services/object_detection_service.py",
        "services/traffic_light_detection_service.py",
        "services/sign_detection_service.py",
        "services/sign_classification_service.py",
        "services/cv_lane_detection_service.py",
        "services/yolop_service.py",
    ]
    all_ok = True
    for ep in entrypoints:
        p = PROJECT_ROOT / ep
        if p.exists():
            _ok(ep)
        else:
            _fail(f"{ep}  - MISSING")
            all_ok = False
    return all_ok


def check_beamng_home():
    print("\n── BeamNG home ──────────────────────────────────────────")
    home = os.environ.get("BEAMNG_HOME", "")
    if home and pathlib.Path(home).exists():
        _ok(f"BEAMNG_HOME = {home}")
    elif home:
        _warn(f"BEAMNG_HOME is set but path does not exist: {home}")
    else:
        _warn("BEAMNG_HOME not set - BeamNG simulation will not run")
        _warn("Set it with:  $env:BEAMNG_HOME = 'C:\\Path\\To\\BeamNG.tech.vX.X'")


def check_model_files():
    print("\n── Model files (optional) ───────────────────────────────")
    models = [
        "models/object_detection/object_detection.pt",
        "models/traffic_light/traffic_light_detection.pt",
        "models/traffic_sign/traffic_sign_detection.pt",
        "models/traffic_sign/traffic_sign_classification.h5",
        "models/yolop/yolop.pt",
    ]
    any_found = False
    for m in models:
        p = PROJECT_ROOT / m
        if p.exists():
            _ok(m)
            any_found = True
        else:
            _warn(f"{m}  - not present (service will fail at inference)")
    if not any_found:
        _warn("No model weights found - services will start but cannot infer")


def check_src_imports():
    """Try importing a few key internal modules."""
    print("\n── Internal module imports ──────────────────────────────")
    sys.path.insert(0, str(PROJECT_ROOT))

    mods = [
        ("config.config",                             "config.config"),
        ("src.communication.aggregator",              "aggregator package"),
        ("src.perception.lane_detection.main",        "CV lane detection"),
        ("src.perception.object_detection.main",      "object detection"),
        ("src.perception.sign_detection.detect_classify", "sign detection"),
        ("src.perception.traffic_light_detection.main",   "traffic light detection"),
    ]

    all_ok = True
    for mod, label in mods:
        try:
            importlib.import_module(mod)
            _ok(label)
        except ImportError as e:
            _fail(f"{label}  →  {e}")
            all_ok = False
        except Exception as e:
            _warn(f"{label}  →  import OK but initialisation error: {e}")
    return all_ok


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  VisionPilot - Environment Verification")
    print("=" * 60)

    results = {
        "Python version": check_python_version(),
        "Required packages": check_required_imports(),
        "Config files": check_config_files(),
        "Config YAML loads": check_config_loads(),
        "Entrypoints": check_entrypoints(),
        "Internal imports": check_src_imports(),
    }

    # non-blocking checks (no pass/fail)
    check_platform()
    check_optional_imports()
    check_beamng_home()
    check_model_files()

    print("\n── Summary ──────────────────────────────────────────────")
    all_ok = True
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        symbol = "OK  " if ok else "FAIL"
        print(f"  [{symbol}] {name}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n  All critical checks passed.")
        print("  Run setup_windows.ps1 to install any missing optional packages.")
    else:
        print("\n  Some checks FAILED. Fix the issues above and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
