import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"
IMAGES_DIR = BASE_DIR / "images"
VIDEOS_DIR = BASE_DIR / "videos"

OBJECT_DETECTION_MODEL = MODELS_DIR / "object_detection" / "object_detection.pt"
SIGN_DETECTION_MODEL = MODELS_DIR / "traffic_sign" / "traffic_sign_detection.pt"
SIGN_CLASSIFICATION_MODEL = MODELS_DIR / "traffic_sign" / "traffic_sign_classification.h5"
LIGHT_DETECTION_CLASSIFICATION_MODEL = MODELS_DIR / "traffic_light" / "traffic_light_detection.pt"
YOLOP_MODEL = MODELS_DIR / "yolop" / "yolop.pt"

# BEAMNG_HOME: prefer the environment variable so different machines work
# without editing this file. Falls back to the dev default if the var is unset.
BEAMNG_HOME = os.environ.get(
    "BEAMNG_HOME",
    r'C:\Users\user\Documents\beamng-tech\BeamNG.tech.v0.37.6.0'
)
