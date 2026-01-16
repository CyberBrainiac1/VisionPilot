import json
import os
import shutil
import random
import yaml
from pathlib import Path
from tqdm import tqdm
from ultralytics import YOLO

INPUT_ROOT = Path('/kaggle/input/bdd-dataset-100k')
TRAIN_IMAGES_DIRS = [
    INPUT_ROOT / 'bdd100k/images/100k/train/trainA',
    INPUT_ROOT / 'bdd100k/images/100k/train/trainB'
]
VAL_IMAGES_DIR = INPUT_ROOT / 'bdd100k/images/100k/val'
TRAIN_LABELS_JSON = INPUT_ROOT / 'labels/bdd100k_labels_images_train.json'
VAL_LABELS_JSON = INPUT_ROOT / 'labels/bdd100k_labels_images_val.json'

WORKING_DIR = Path('/kaggle/working')
DATASET_DIR = WORKING_DIR / 'bdd100k_yolo'
IMAGES_DIR = DATASET_DIR / 'images'
LABELS_DIR = DATASET_DIR / 'labels'

for split in ['train', 'val']:
    (IMAGES_DIR / split).mkdir(parents=True, exist_ok=True)
    (LABELS_DIR / split).mkdir(parents=True, exist_ok=True)

CLASS_MAPPING = {
    'car': 0,
    'bus': 1,
    'truck': 2,
    'bike': 3,       # Bicycle
    'motor': 4,      # Motorcycle
    'traffic sign': 5,
    'traffic light': 6,
    'person': 7,
    'rider': 8
}

CLASSES = list(CLASS_MAPPING.keys())

IMG_SIZE = 640
BATCH_SIZE = 32
EPOCHS = 100
PATIENCE = 20
RESUME_FROM_CHECKPOINT = True
CHECKPOINT_PATH = '/kaggle/input/checkpoint-objdet/other/objectdetyolom/1/last.pt'

def convert_box_to_yolo(box2d, img_width=1280, img_height=720):
    """
    Convert BDD100K box2d (x1, y1, x2, y2) to YOLO format (x_center, y_center, width, height) normalized.
    BDD100K images are typically 1280x720.
    """
    x1 = box2d['x1']
    y1 = box2d['y1']
    x2 = box2d['x2']
    y2 = box2d['y2']

    w = x2 - x1
    h = y2 - y1
    cx = x1 + (w / 2)
    cy = y1 + (h / 2)

    cx /= img_width
    cy /= img_height
    w /= img_width
    h /= img_height

    cx = max(0, min(1, cx))
    cy = max(0, min(1, cy))
    w = max(0, min(1, w))
    h = max(0, min(1, h))

    return cx, cy, w, h

def process_dataset(json_path, raw_images_dirs, split, num_samples=None):
    """
    Reads annotation JSON, selects a subset, creates label files, and copies images.
    raw_images_dirs can be a single Path or a list of Paths (for trainA/trainB).
    """
    if not isinstance(raw_images_dirs, list):
        raw_images_dirs = [raw_images_dirs]
    
    print(f"Processing {split} dataset...")
    
    with open(json_path, 'r') as f:
        data = json.load(f)

    if num_samples:
        random.seed(42)
        random.shuffle(data)
        data = data[:num_samples]
    
    print(f"Converting {len(data)} images for {split}...")

    for item in tqdm(data):
        image_name = item['name']
        labels = item.get('labels', [])
        
        yolo_labels = []
        
        for label in labels:
            category = label['category']
            
            if category not in CLASS_MAPPING:
                continue
            
            if 'box2d' not in label:
                continue
                
            cls_id = CLASS_MAPPING[category]
            cx, cy, w, h = convert_box_to_yolo(label['box2d'])
            
            yolo_labels.append(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        
        if yolo_labels:
            label_filename = Path(image_name).with_suffix('.txt').name
            with open(LABELS_DIR / split / label_filename, 'w') as lf:
                lf.write('\n'.join(yolo_labels))
            
            src_image_path = None
            for images_dir in raw_images_dirs:
                potential_path = images_dir / image_name
                if potential_path.exists():
                    src_image_path = potential_path
                    break
            
            if src_image_path:
                dst_image_path = IMAGES_DIR / split / image_name
                shutil.copy(src_image_path, dst_image_path)
            else:
                print(f"Warning: Image {image_name} not found in any source directory.")

def create_data_yaml():
    yaml_content = {
        'path': str(DATASET_DIR.absolute()),
        'train': 'images/train',
        'val': 'images/val',
        'names': {v: k for k, v in CLASS_MAPPING.items()}
    }
    
    yaml_path = WORKING_DIR / 'bdd100k.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, sort_keys=False)
    
    return yaml_path

if __name__ == '__main__':
    print("Clearing old dataset")
    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR)
    if LABELS_DIR.exists():
        shutil.rmtree(LABELS_DIR)
    
    for split in ['train', 'val']:
        (IMAGES_DIR / split).mkdir(parents=True, exist_ok=True)
        (LABELS_DIR / split).mkdir(parents=True, exist_ok=True)
    
    if TRAIN_LABELS_JSON.exists():
        process_dataset(TRAIN_LABELS_JSON, TRAIN_IMAGES_DIRS, 'train', num_samples=None)
    else:
        print(f"Error: Training labels not found at {TRAIN_LABELS_JSON}")

    if VAL_LABELS_JSON.exists():
        process_dataset(VAL_LABELS_JSON, VAL_IMAGES_DIR, 'val', num_samples=None) 
    else:
        print(f"Error: Validation labels not found at {VAL_LABELS_JSON}")

    yaml_path = create_data_yaml()
    print(f"Data config created at: {yaml_path}")

    if RESUME_FROM_CHECKPOINT:
        print(f"Resuming training from checkpoint: {CHECKPOINT_PATH}")
        model = YOLO(CHECKPOINT_PATH)
    else:
        print("Starting Training with YOLOv11m from scratch")
        model = YOLO('yolov11m.pt')

    results = model.train(
        data=str(yaml_path),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        patience=PATIENCE,   # Early stopping
        project='bdd100k_training',
        name='yolov11m_full_100k',
        exist_ok=True,       # Overwrite existing run
        device=0,
        verbose=True
    )
    
    print("Training Complete.")
