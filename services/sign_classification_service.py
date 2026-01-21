import os
import sys
import numpy as np
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core sign classification logic from source
from src.perception.sign_detection.detect_classify import sign_classification_only

app = Flask(__name__)

MODELS = {}

def load_models():
    """Initialize classification model"""
    global MODELS
    model_path = os.getenv('MODEL_PATH')
    if not model_path:
        print("[Sign Classification Service] ERROR: MODEL_PATH environment variable not set")
        return False
    
    if not os.path.exists(model_path):
        print(f"[Sign Classification Service] ERROR: Model file not found at {model_path}")
        return False
    
    print(f"[Sign Classification Service] Model path configured: {model_path}")
    MODELS['model_path'] = model_path
    print("[Sign Classification Service] Ready to process frames")
    return True

@app.route('/process', methods=['POST'])
def process_classification():
    """
    Process bounding boxes for traffic sign classification only
    
    Expected JSON payload:
    {
        "frame": [list of pixel values],
        "frame_shape": [height, width, channels],
        "bboxes": [[x1, y1, x2, y2], ...],  # Optional: pre-detected bboxes
        "frame_id": "frame_123"
    }
    """
    try:
        data = request.get_json()
        
        # decode frame from request
        frame_data = np.array(data['frame'], dtype=np.uint8)
        frame_shape = data.get('frame_shape', [1080, 1920, 3])
        frame = frame_data.reshape(frame_shape)
        
        # try to use pre-detected bboxes if provided
        bboxes = data.get('bboxes', None)
        if bboxes:
            bboxes = [tuple(bbox) for bbox in bboxes]
        
        frame_id = data.get('frame_id', 'unknown')
        
        print(f"[Sign Classification Service] Processing frame {frame_id}: {frame.shape}, bboxes: {len(bboxes) if bboxes else 'auto-detect'}")
        
        # call classification logic
        classifications = sign_classification_only(frame, bboxes=bboxes)
        
        # format classifications for response
        formatted_classifications = []
        if classifications:
            for cls in classifications:
                formatted_classifications.append({
                    'sign_type': cls.get('classification', 'unknown'),
                    'confidence': float(cls.get('classification_confidence', 0.0)),
                    'class_index': int(cls.get('class_index', -1)),
                    'bbox': list(cls.get('bbox', [0, 0, 0, 0]))
                })
        
        response = {
            'frame_id': frame_id,
            'service': 'sign_classification',
            'status': 'success',
            'classifications': formatted_classifications,
            'classification_count': len(formatted_classifications)
        }
        
        return response, 200
        
    except Exception as e:
        print(f"[Sign Classification Service] Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e), 'frame_id': data.get('frame_id', 'unknown')}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'sign_classification',
        'model_configured': MODELS.get('model_path') is not None
    }, 200

if __name__ == '__main__':
    if not load_models():
        print("[Sign Classification Service] Failed to load models. Exiting.")
        sys.exit(1)
    print("[Sign Classification Service] Starting on 0.0.0.0:8777")
    app.run(host='0.0.0.0', port=8777, debug=False)
