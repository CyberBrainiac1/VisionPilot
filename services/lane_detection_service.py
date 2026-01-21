import os
import sys
import numpy as np
import torch
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.perception.lane_detection.main import process_frame_scnn
from src.perception.lane_detection.scnn.scnn_model import SCNN

app = Flask(__name__)

MODELS = {}

def load_models():
    global MODELS
    model_path = os.getenv('MODEL_PATH')
    if not model_path:
        print("[Lane Detection Service] ERROR: MODEL_PATH environment variable not set")
        return False
    
    if not os.path.exists(model_path):
        print(f"[Lane Detection Service] ERROR: Model file not found at {model_path}")
        return False
    
    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = SCNN(input_size=512, pretrained=False)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model = model.to(device)
        model.eval()
        
        MODELS['model'] = model
        MODELS['device'] = device
        print(f"[Lane Detection Service] Model loaded from {model_path} on {device}")
        return True
    except Exception as e:
        print(f"[Lane Detection Service] ERROR loading model: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/process', methods=['POST'])
def process():
    """
    Process a camera frame for lane detection using SCNN
    
    Expected JSON payload:
    {
        "frame": [list of pixel values],
        "frame_shape": [height, width, channels],
        "speed_kph": 50.0,
        "previous_steering": 0.1,
        "frame_id": "frame_123"
    }
    """
    try:
        data = request.get_json()
        
        # decode frame from request
        frame_data = np.array(data['frame'], dtype=np.uint8)
        frame_shape = data.get('frame_shape', [1080, 1920, 3])
        frame = frame_data.reshape(frame_shape)
        
        speed_kph = data.get('speed_kph', 0.0)
        previous_steering = data.get('previous_steering', 0.0)
        frame_id = data.get('frame_id', 'unknown')
        
        print(f"[Lane Detection Service] Processing frame {frame_id}: {frame.shape}, speed: {speed_kph} km/h")
        
        model = MODELS.get('model')
        device = MODELS.get('device')
        if model is None or device is None:
            return {'status': 'error', 'message': 'Model not loaded', 'frame_id': frame_id}, 500
        
        result_img, metrics = process_frame_scnn(
            frame,
            model=model,
            device=device,
            speed=speed_kph,
            previous_steering=previous_steering,
            debug_display=False
        )
        
        # extract relevant metrics for response
        response = {
            'frame_id': frame_id,
            'service': 'lane_detection_scnn',
            'status': 'success',
            'metrics': {
                'confidence': float(metrics.get('confidence', 0.0)),
                'left_curvature': float(metrics.get('left_curvature', 0.0)) if metrics.get('left_curvature') else None,
                'right_curvature': float(metrics.get('right_curvature', 0.0)) if metrics.get('right_curvature') else None,
                'deviation': float(metrics.get('deviation', 0.0)) if metrics.get('deviation') else None,
                'lane_center': float(metrics.get('lane_center', 0.0)) if metrics.get('lane_center') else None,
                'vehicle_center': float(metrics.get('vehicle_center', 0.0)) if metrics.get('vehicle_center') else None,
            }
        }
        
        return response, 200
        
    except Exception as e:
        print(f"[Lane Detection Service] Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e), 'frame_id': data.get('frame_id', 'unknown')}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'lane_detection_scnn',
        'model_configured': MODELS.get('model_path') is not None
    }, 200

if __name__ == '__main__':
    if not load_models():
        print("[Lane Detection Service] Failed to load models. Exiting.")
        sys.exit(1)
    print("[Lane Detection Service] Starting on 0.0.0.0:4777")
    app.run(host='0.0.0.0', port=4777, debug=False)