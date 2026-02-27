import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.perception.lane_detection.cv.thresholding import apply_thresholds_with_voting
from src.perception.lane_detection.cv.perspective import debug_perspective_live, get_src_points, perspective_warp
from src.perception.lane_detection.cv.lane_finder import get_histogram, detect_lane_type, fill_dashed_lane_gaps
from src.perception.lane_detection.metrics import calculate_curvature_and_deviation
from src.perception.lane_detection.visualization import draw_lane_overlay, add_text_overlay, create_mask_overlay

from src.perception.lane_detection.cv.multi_lane.multi_lane_finder import detect_multiple_lanes
from src.perception.lane_detection.cv.multi_lane.lane_selector import get_current_lane

from src.perception.lane_detection.confidence import compute_confidence_cv


import numpy as np
import cv2


def process_frame_cv(img, speed=0, previous_steering=0, debug_display=False, perspective_debug_display=False, calibration_data=None, vehicle_model='q8_andronisk', num_lanes=3):
        
    previous_fit = None
    confidence = 0.0
    try:

        src_points = get_src_points(img.shape, speed, previous_steering, vehicle_model=vehicle_model, calibration_data=calibration_data)

        # Apply thresholding to FULL image
        binary_image, avg_brightness = apply_thresholds_with_voting(
            img, 
            src_points=None,
            debug_display=debug_display,
            use_gradient=False
        )
        if debug_display:
            cv2.imshow('Binary Image CV', binary_image*255 if binary_image.max()<=1 else binary_image)
            cv2.waitKey(1)

        # Apply roi mask
        mask = np.zeros(binary_image.shape[:2], dtype=np.uint8)
        src_poly = np.array(src_points, dtype=np.int32)
        cv2.fillPoly(mask, [src_poly], 1)
        binary_image = binary_image * mask
        
        # perspective warp for BEV
        binary_warped, Minv = perspective_warp(binary_image, speed=speed, calibration_data=calibration_data, vehicle_model=vehicle_model)

        is_dashed_lane = detect_lane_type(binary_warped)
        if is_dashed_lane:
            binary_warped = fill_dashed_lane_gaps(binary_warped, gap_size=20)
        
        if perspective_debug_display:
            debug_perspective_live(img, speed, previous_steering=0, vehicle_model=vehicle_model, calibration_data=calibration_data)
        
        if debug_display:
            warped_display = np.dstack((binary_warped, binary_warped, binary_warped)) * 255
            cv2.imshow('Warped Binary CV', warped_display)

        lanes = None
        detected_num_lanes = num_lanes

        for attempt_lanes in [num_lanes, num_lanes-1, 2, 1]:
            if attempt_lanes < 1:
                break
            lanes = detect_multiple_lanes(binary_warped, num_lanes=attempt_lanes)
            if lanes is not None:
                detected_num_lanes = attempt_lanes
                print(f"Successfully detected {detected_num_lanes} lanes")
                break
            else:
                print(f"failed to detect {attempt_lanes} lanes, trying with {attempt_lanes-1} lanes")
        

        if lanes is None:
            print("multi-lane detection failed")
            result = img.copy()
            metrics = {
                'current_lane': None,
                'all_lanes': None,
                'confidence': 0.0,
                'error': 'Multi-lane detection failed'
            }
            return result, metrics, 0.0
        
        # classify lanes and get current lane
        lane_info = get_current_lane(lanes, vehicle_center=None, image_width=img.shape[1])
        current_lane_data = lane_info['current_lane']
        all_lanes = lane_info['classified_lanes']

        # extract left and right fitx
        # Use current lane or fallback to first lane
        if current_lane_data:
            lane_data = current_lane_data['lane_data']
        else:
            # Fallback to first lane if no current lane detected
            first_lane = list(all_lanes.values())[0] if all_lanes else None
            if first_lane:
                lane_data = first_lane['lane_data']
            else:
                print("No lane data available")
                result = img.copy()
                metrics = {
                    'current_lane': None,
                    'all_lanes': None,
                    'confidence': 0.0,
                    'error': 'No lane data'
                }
                return result, metrics, 0.0
        
        # extract data
        ploty = lane_data['ploty']
        left_fitx = lane_data['left_fitx']
        right_fitx = lane_data['right_fitx']
        left_fit = lane_data['left_fit']
        right_fit = lane_data['right_fit']
        
        # keep drawing method
        result = draw_lane_overlay(img, binary_warped, Minv, left_fitx, right_fitx, ploty, deviation=0)
        
        # Calculate metrics
        current_fit = (left_fit, right_fit)
        metrics_result = calculate_curvature_and_deviation(ploty, left_fitx, right_fitx, binary_warped, original_image_width=img.shape[1])

        confidence = compute_confidence_cv(left_fitx, right_fitx, ploty, current_fit=current_fit, previous_fit=previous_fit)
        previous_fit = current_fit

        if metrics_result is None or (isinstance(metrics_result, tuple) and all(x is None for x in metrics_result)):
            left_curverad, right_curverad, deviation, lane_center, vehicle_center, lane_width = None, None, None, None, None, None
            print("Lane detection metrics calculation returned None values")
        else:
            if len(metrics_result) == 6:
                left_curverad, right_curverad, deviation, lane_center, vehicle_center, lane_width = metrics_result
            elif len(metrics_result) == 5:
                left_curverad, right_curverad, deviation, lane_center, vehicle_center = metrics_result
                lane_width = None
            else:
                left_curverad, right_curverad, deviation, lane_center, vehicle_center, lane_width = None, None, None, None, None, None

        result = add_text_overlay(result, left_curverad, right_curverad, deviation, avg_brightness, speed, confidence=confidence)
        
        metrics = {
            'left_curverad': left_curverad,
            'right_curverad': right_curverad,
            'deviation': deviation,
            'lane_center': lane_center,
            'vehicle_center': vehicle_center,
            'lane_width': lane_width,
            'confidence': confidence,
            'current_lane': current_lane_data,
            'all_lanes': all_lanes,
            'detected_num_lanes': detected_num_lanes
        }
        
        return result, metrics, confidence
        
    except Exception as e:
        print(f"Lane detection error CV: {e}")
        import traceback
        traceback.print_exc()
        result = img.copy()
        metrics = {
            'left_curverad': 0,
            'right_curverad': 0,
            'deviation': 0,
            'lane_center': 0,
            'vehicle_center': 0,
            'lane_width': 0,
            'confidence': 0,
            'current_lane': None,
            'all_lanes': None,
            'error': str(e)
        }
        return result, metrics, 0.0

