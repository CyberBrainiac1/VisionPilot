import os
import sys
import numpy as np
from flask import Flask, request, jsonify

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import core logic from src
from src.perception.lane_detection.main import process_frame_scnn

app = Flask(__name__)

MODEL_INFO = None

def load_models():
    """Load SCNN model once at startup (handled by process_frame_scnn internally)"""
    global MODEL_INFO
    model_path = os.getenv('MODEL_PATH', '/app/models/lane_detection/scnn.pth')
    print(f"[Lane Detection Service] Model path configured: {model_path}")
    MODEL_INFO = {'path': model_path}
    print(f"[Lane Detection Service] Ready to process frames")

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
        
        # Decode frame from request
        frame_data = np.array(data['frame'], dtype=np.uint8)
        frame_shape = data.get('frame_shape', [720, 1280, 3])
        frame = frame_data.reshape(frame_shape)
        
        speed_kph = data.get('speed_kph', 0.0)
        previous_steering = data.get('previous_steering', 0.0)
        frame_id = data.get('frame_id', 'unknown')
        
        print(f"[Lane Detection Service] Processing frame {frame_id}: {frame.shape}, speed: {speed_kph} km/h")
        
        # call core inference logic from source
        result_img, metrics = process_frame_scnn(
            frame, 
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
        'model_configured': MODEL_INFO is not None
    }, 200

if __name__ == '__main__':
    load_models()
    print("[Lane Detection Service] Starting on 0.0.0.0:4777")
    app.run(host='0.0.0.0', port=4777, debug=False)