from pathlib import Path
import os
import torch
import cv2
from PIL import Image
import numpy as np
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
import json

# Mapillary Vistas official class names and IDs (66 classes)
MAPILLARY_VISTAS_CLASSES = {
    0: 'Bird',
    1: 'Ground Animal',
    2: 'Curb',
    3: 'Fence',
    4: 'Guard Rail',
    5: 'Barrier',
    6: 'Wall',
    7: 'Bike Lane',
    8: 'Crosswalk - Plain',
    9: 'Curb Cut',
    10: 'Parking',
    11: 'Pedestrian Area',
    12: 'Rail Track',
    13: 'Road',
    14: 'Service Lane',
    15: 'Sidewalk',
    16: 'Bridge',
    17: 'Building',
    18: 'Tunnel',
    19: 'Person',
    20: 'Bicyclist',
    21: 'Motorcyclist',
    22: 'Other Rider',
    23: 'Lane Marking - Crosswalk',
    24: 'Lane Marking - General',
    25: 'Mountain',
    26: 'Sand',
    27: 'Sky',
    28: 'Snow',
    29: 'Terrain',
    30: 'Vegetation',
    31: 'Water',
    32: 'Banner',
    33: 'Bench',
    34: 'Bike Rack',
    35: 'Billboard',
    36: 'Catch Basin',
    37: 'CCTV Camera',
    38: 'Fire Hydrant',
    39: 'Junction Box',
    40: 'Mailbox',
    41: 'Manhole',
    42: 'Phone Booth',
    43: 'Pothole',
    44: 'Street Light',
    45: 'Pole',
    46: 'Traffic Sign Frame',
    47: 'Utility Pole',
    48: 'Traffic Light',
    49: 'Traffic Sign (Back)',
    50: 'Traffic Sign (Front)',
    51: 'Trash Can',
    52: 'Bicycle',
    53: 'Boat',
    54: 'Bus',
    55: 'Car',
    56: 'Caravan',
    57: 'Motorcycle',
    58: 'On Rails',
    59: 'Other Vehicle',
    60: 'Trailer',
    61: 'Truck',
    62: 'Wheeled Slow',
    63: 'Car Mount',
    64: 'Ego Vehicle',
}

def get_colormap(num_classes):
    """Generate a distinct colormap for all classes."""
    np.random.seed(42)  # For reproducibility
    colors = np.random.randint(50, 255, size=(num_classes, 3), dtype=np.uint8)
    # Make sure first class (Bird) is dark
    colors[0] = [0, 0, 0]
    return colors

PALETTE = get_colormap(len(MAPILLARY_VISTAS_CLASSES))

def colorize_segmentation(seg_map):
    """Convert segmentation map to colored image."""
    colored = np.zeros((seg_map.shape[0], seg_map.shape[1], 3), dtype=np.uint8)
    for cls_id in range(len(PALETTE)):
        mask = seg_map == cls_id
        colored[mask] = PALETTE[cls_id]
    return colored

def create_legend(output_dir):
    """Create and save a legend image showing class names and colors."""
    num_classes = len(MAPILLARY_VISTAS_CLASSES)
    
    # Create legend image (10 columns, height based on classes)
    cols = 10
    rows = (num_classes + cols - 1) // cols
    cell_width, cell_height = 200, 30
    
    legend_img = np.ones((rows * cell_height, cols * cell_width, 3), dtype=np.uint8) * 255
    
    for class_id in range(num_classes):
        class_name = MAPILLARY_VISTAS_CLASSES[class_id]
        row = class_id // cols
        col = class_id % cols
        y = row * cell_height
        x = col * cell_width
        
        # Draw colored rectangle
        color = tuple(int(c) for c in PALETTE[class_id])
        cv2.rectangle(legend_img, (x, y), (x + 40, y + cell_height), color, -1)
        
        # Draw class name
        cv2.putText(legend_img, f"{class_id}: {class_name[:15]}", (x + 50, y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    legend_path = Path(output_dir) / "class_legend.png"
    cv2.imwrite(str(legend_path), legend_img)
    print(f"Saved class legend to {legend_path}")
    
    # Also save as JSON for reference
    class_info = {
        str(class_id): {"name": MAPILLARY_VISTAS_CLASSES[class_id], "color": PALETTE[class_id].tolist()}
        for class_id in range(num_classes)
    }
    json_path = Path(output_dir) / "class_info.json"
    with open(json_path, 'w') as f:
        json.dump(class_info, f, indent=2)
    print(f"Saved class info to {json_path}")

cameras = ['camera_front', 'camera_left', 'camera_right', 'camera_rear']

def segment_all_camera(raw_base, output_base, device='cuda'):
    """
    Run semantic segmentation on all camera images using Mask2Former.
    
    Args:
        raw_base (str): Path to raw data directory containing camera subdirectories
        output_base (str): Path to output directory where segmented images will be saved
        device (str): Device to run inference on ('cuda' or 'cpu')
    """
    # Load model and processor
    print("Loading Mask2Former model...")
    processor = AutoImageProcessor.from_pretrained("facebook/mask2former-swin-large-mapillary-vistas-semantic")
    model = Mask2FormerForUniversalSegmentation.from_pretrained("facebook/mask2former-swin-large-mapillary-vistas-semantic").to(device)
    
    output_base_path = Path(output_base)
    output_base_path.mkdir(parents=True, exist_ok=True)  # Create base directory first
    
    # Create and save legend (only once)
    create_legend(output_base_path)
    
    for cam in cameras:
        input_dir = Path(raw_base) / cam
        output_dir_overlay = output_base_path / cam / "overlay"
        output_dir_raw = output_base_path / cam / "raw"
        output_dir_overlay.mkdir(parents=True, exist_ok=True)
        output_dir_raw.mkdir(parents=True, exist_ok=True)
        images = sorted(input_dir.glob('*.png')) + sorted(input_dir.glob('*.jpg'))
        if not images:
            print(f"No images found in {input_dir}, skipping.")
            continue
        
        print(f"Processing {len(images)} images from {cam}...")
        for img_path in images:
            segment_image(img_path, output_dir_overlay, output_dir_raw, model, processor, device)
        
        print(f"Completed {cam}")


def segment_image(img_path, output_dir_overlay, output_dir_raw, model, processor, device):
    """
    Run semantic segmentation on a single image.
    
    Args:
        img_path (Path or str): Path to input image
        output_dir_overlay (Path): Directory to save overlay segmented image
        output_dir_raw (Path): Directory to save raw mask (no original image)
        model: Mask2Former model
        processor: Image processor
        device (str): Device to run inference on
    """
    image = Image.open(str(img_path)).convert("RGB")
    original_size = image.size
    
    # Preprocess
    inputs = processor(images=image, return_tensors="pt").to(device)
    
    # Inference
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Post-process for semantic segmentation
    predicted_seg = processor.post_process_semantic_segmentation(outputs, target_sizes=[original_size[::-1]])[0]
    predicted_seg = np.array(predicted_seg.cpu())
    
    # Colorize
    colored_seg = colorize_segmentation(predicted_seg)
    image_cv = cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_BGR2RGB)
    overlay = cv2.addWeighted(image_cv, 0.7, colored_seg, 0.3, 0)
    overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    
    # Save raw mask
    colored_seg_bgr = cv2.cvtColor(colored_seg, cv2.COLOR_RGB2BGR)
    
    output_name = Path(img_path).stem
    
    # Save overlay
    overlay_path = Path(output_dir_overlay) / f"{output_name}.png"
    cv2.imwrite(str(overlay_path), overlay_bgr)
    
    # Save raw mask
    raw_path = Path(output_dir_raw) / f"{output_name}.png"
    cv2.imwrite(str(raw_path), colored_seg_bgr)
