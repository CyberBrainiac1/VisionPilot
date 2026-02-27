import os
import sys
import numpy as np
from flask import Flask, request, jsonify
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core detection logic from source
from src.perception.lane_detection.main import process_frame_cv

app = Flask(__name__)

MODELS = {}


def load_models():
    """Initialize lane detection (no external model needed for CV)"""
    print("[CV Lane Detection Service] Model initialization - CV-based detection (no external model)")
    print("[CV Lane Detection Service] Ready to process frames")
    return True


@app.route('/process', methods=['POST'])
def process_lane_detection():
    """
    Process a camera frame for lane detection using CV methods
    
    Expected JSON payload:
    {
        "frame": [list of pixel values],
        "frame_shape": [height, width, channels],
        "speed_kph": 50.0,
        "frame_id": "frame_123"
    }
    
    Returns:
    {
        "frame_id": "frame_123",
        "service": "cv_lane_detection",
        "status": "success",
        "metrics": {
            "deviation": float,
            "lane_center": float,
            "vehicle_center": float,
            "confidence": float,
            ...
        },
        "result_image": [resized image as array]
    }
    """
    try:
        data = request.get_json()
        
        # Decode frame from request
        frame_data = np.array(data['frame'], dtype=np.uint8)
        frame_shape = data.get('frame_shape', [1080, 1920, 3])
        frame = frame_data.reshape(frame_shape)
        
        speed_kph = data.get('speed_kph', 0.0)
        frame_id = data.get('frame_id', 'unknown')
        
        print(f"[CV Lane Detection Service] Processing frame {frame_id}: {frame.shape}, speed: {speed_kph:.1f} kph")
        
        # Call CV lane detection
        result_img, metrics, confidence = process_frame_cv(
            frame,
            speed=speed_kph,
            previous_steering=0,
            debug_display=False,
            perspective_debug_display=False,
            calibration_data=None,
            vehicle_model='q8_andronisk',
            num_lanes=3
        )
        
        # Prepare response
        response = {
            'frame_id': frame_id,
            'service': 'cv_lane_detection',
            'status': 'success',
            'metrics': {
                'deviation': float(metrics.get('deviation', 0.0)),
                'lane_center': float(metrics.get('lane_center', 0.0)),
                'vehicle_center': float(metrics.get('vehicle_center', 0.0)),
                'confidence': float(metrics.get('confidence', 0.0)),
                'left_curverad': float(metrics.get('left_curverad', 0.0)) if metrics.get('left_curverad') else None,
                'right_curverad': float(metrics.get('right_curverad', 0.0)) if metrics.get('right_curverad') else None,
                'lane_width': float(metrics.get('lane_width', 0.0)) if metrics.get('lane_width') else None,
                'detected_num_lanes': int(metrics.get('detected_num_lanes', 0))
            }
        }
        
    except Exception as e:
        print(f"[CV Lane Detection Service] Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': str(e),
            'frame_id': data.get('frame_id', 'unknown')
        }, 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'cv_lane_detection',
        'description': 'OpenCV-based lane detection'
    }, 200


if __name__ == '__main__':
    print("[CV Lane Detection Service] Starting...")
    
    if not load_models():
        print("[CV Lane Detection Service] Failed to initialize, exiting")
        sys.exit(1)
    
    print("[CV Lane Detection Service] Listening on 0.0.0.0:4777")
    app.run(host='0.0.0.0', port=4777, debug=False, threaded=True)
