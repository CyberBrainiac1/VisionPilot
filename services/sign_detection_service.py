import os
import sys
import numpy as np
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core sign detection logic from source
from src.perception.sign_detection.detect_classify import sign_detection_only

app = Flask(__name__)

def load_models():
    """Initialize detection model (handled internally)"""
    print("[Sign Detection Service] Ready to process frames")

@app.route('/process', methods=['POST'])
def process_detection():
    """
    Process a camera frame for traffic sign detection (no classification)
    
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
        frame_shape = data.get('frame_shape', [720, 1280, 3])
        frame = frame_data.reshape(frame_shape)
        
        confidence_threshold = data.get('confidence_threshold', 0.2)
        frame_id = data.get('frame_id', 'unknown')
        
        print(f"[Sign Detection Service] Processing frame {frame_id}: {frame.shape}, threshold: {confidence_threshold}")
        
        # Call core detection-only logic from source
        detections = sign_detection_only(frame, confidence_threshold=confidence_threshold)
        
        # Format detections for response
        formatted_detections = []
        if detections:
            for det in detections:
                formatted_detections.append({
                    'detection_class': det.get('detection_class', 'unknown'),
                    'detection_confidence': float(det.get('detection_confidence', 0.0)),
                    'bbox': list(det.get('bbox', [0, 0, 0, 0]))
                })
        
        response = {
            'frame_id': frame_id,
            'service': 'sign_detection',
            'status': 'success',
            'detections': formatted_detections,
            'detection_count': len(formatted_detections)
        }
        
        return response, 200
        
    except Exception as e:
        print(f"[Sign Detection Service] Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e), 'frame_id': data.get('frame_id', 'unknown')}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'sign_detection'
    }, 200

if __name__ == '__main__':
    load_models()
    print("[Sign Detection Service] Starting on 0.0.0.0:7777")
    app.run(host='0.0.0.0', port=7777, debug=False)
