import os
import sys
import numpy as np
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core detection logic from source
from src.perception.object_detection.main import process_frame

app = Flask(__name__)

def load_models():
    """Initialize detection model (handled by process_frame internally)"""
    print("[Object Detection Service] Ready to process frames")

@app.route('/process', methods=['POST'])
def process_detection():
    """
    Process a camera frame for vehicle/pedestrian detection
    
    Expected JSON payload:
    {
        "frame": [list of pixel values],
        "frame_shape": [height, width, channels],
        "confidence_threshold": 0.4,
        "frame_id": "frame_123"
    }
    """
    try:
        data = request.get_json()
        
        # Decode frame from request
        frame_data = np.array(data['frame'], dtype=np.uint8)
        frame_shape = data.get('frame_shape', [720, 1280, 3])
        frame = frame_data.reshape(frame_shape)
        
        confidence_threshold = data.get('confidence_threshold', 0.4)
        frame_id = data.get('frame_id', 'unknown')
        
        print(f"[Object Detection Service] Processing frame {frame_id}: {frame.shape}, threshold: {confidence_threshold}")
        
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
                    'class': det.get('class', 'unknown'),
                    'confidence': float(det.get('confidence', 0.0)),
                    'bbox': det.get('bbox', [0, 0, 0, 0])
                })
        
        response = {
            'frame_id': frame_id,
            'service': 'object_detection',
            'status': 'success',
            'detections': formatted_detections,
            'detection_count': len(formatted_detections)
        }
        
        return response, 200
        
    except Exception as e:
        print(f"[Object Detection Service] Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e), 'frame_id': data.get('frame_id', 'unknown')}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'object_detection'
    }, 200

if __name__ == '__main__':
    load_models()
    print("[Object Detection Service] Starting on 0.0.0.0:5777")
    app.run(host='0.0.0.0', port=5777, debug=False)
