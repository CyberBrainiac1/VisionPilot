import os
import sys
import numpy as np
from flask import Flask, request, jsonify

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core traffic light detection logic from source
from src.perception.traffic_light_detection.main import process_frame

app = Flask(__name__)

MODELS = {}

def load_models():
    """Initialize detection model"""
    global MODELS
    model_path = os.getenv('MODEL_PATH')
    if not model_path:
        print("[Traffic Light Detection Service] ERROR: MODEL_PATH environment variable not set")
        return False
    
    if not os.path.exists(model_path):
        print(f"[Traffic Light Detection Service] ERROR: Model file not found at {model_path}")
        return False
    
    print(f"[Traffic Light Detection Service] Model path configured: {model_path}")
    MODELS['model_path'] = model_path
    print("[Traffic Light Detection Service] Ready to process frames")
    return True

@app.route('/process', methods=['POST'])
def process_detection():
    """
    Process a camera frame for traffic light detection and classification
    
    Expected JSON payload:
    {
        "frame": [list of pixel values],
        "frame_shape": [height, width, channels],
        "confidence_threshold": 0.2,
        "frame_id": "frame_123"
    }
    """
    try:
        data = request.get_json()
        
        # Decode frame from request
        frame_data = np.array(data['frame'], dtype=np.uint8)
        frame_shape = data.get('frame_shape', [1080, 1920, 3])
        frame = frame_data.reshape(frame_shape)
        
        confidence_threshold = data.get('confidence_threshold', 0.2)
        frame_id = data.get('frame_id', 'unknown')
        
        print(f"[Traffic Light Detection Service] Processing frame {frame_id}: {frame.shape}, threshold: {confidence_threshold}")
        
        # Call core inference logic from source
        detections, result_img = process_frame(
            frame,
            confidence_threshold=confidence_threshold,
            draw_detections=False
        )
        
        # Format detections for response
        formatted_detections = []
        if detections:
            for det in detections:
                formatted_detections.append({
                    'state': det.get('state', 'unknown'),  # e.g., 'red', 'yellow', 'green'
                    'confidence': float(det.get('confidence', 0.0)),
                    'bbox': det.get('bbox', [0, 0, 0, 0])
                })
        
        response = {
            'frame_id': frame_id,
            'service': 'traffic_light_detection',
            'status': 'success',
            'detections': formatted_detections,
            'detection_count': len(formatted_detections)
        }
        
        return response, 200
        
    except Exception as e:
        print(f"[Traffic Light Detection Service] Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e), 'frame_id': data.get('frame_id', 'unknown')}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'traffic_light_detection',
        'model_configured': MODELS.get('model_path') is not None
    }, 200

if __name__ == '__main__':
    if not load_models():
        print("[Traffic Light Detection Service] Failed to load models. Exiting.")
        sys.exit(1)
    print("[Traffic Light Detection Service] Starting on 0.0.0.0:6777")
    app.run(host='0.0.0.0', port=6777, debug=False)
