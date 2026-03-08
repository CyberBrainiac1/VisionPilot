import numpy as np
import cv2



def add_text_overlay(image, left_curverad, right_curverad, deviation, avg_brightness, speed, confidence):
    """
    Add text overlay with lane curvature, deviation, average brightness, and speed.
    Args:
        image: Image to add text overlay on
        left_curverad: Left lane line curvature in meters
        right_curverad: Right lane line curvature in meters
        deviation: Vehicle deviation from lane center in meters
        avg_brightness: Average brightness of the image
        speed: Vehicle speed in km/h
        confidence: Confidence score of lane detection (0.0 to 1.0)
    Returns:
        Image with text overlay
    """

    fontType = cv2.FONT_HERSHEY_SIMPLEX
    
    if deviation is None:
        deviation_text = "Deviation: N/A"
    else:
        direction = '+' if deviation > 0 else '-'
        deviation_text = f"Deviation: {direction}{abs(deviation):.2f}m"
    
    cv2.putText(image, deviation_text, (30, 50), fontType, 0.4, (0, 0, 0), 1)

    cv2.putText(image, f"Avg Brightness: {avg_brightness:.1f}", (30, 80), fontType, 0.4, (0, 0, 0), 1)

    if confidence is not None:
        cv2.putText(image, f"Confidence: {confidence:.2f}", (30, 110), fontType, 0.4, (0, 0, 0), 1)
    else:
        cv2.putText(image, "Confidence: N/A", (30, 110), fontType, 0.4, (0, 0, 0), 1)

    
    return image

def draw_multi_lane_overlay(original_image, binary_warped, Minv, all_lanes, current_lane_data):
    """
    Draw all detected lanes on the original image with labels.
    
    Args:
        original_image: Original image to draw on
        binary_warped: Warped binary image (for rotation info)
        Minv: Inverse perspective transform matrix
        all_lanes: Dictionary of all detected lanes with classification (left, center, right)
        current_lane_data: Current lane info for labeling
    
    Returns:
        Image with all lanes drawn and labeled
    """
    result = original_image.copy()
    
    lane_colors = {
        'left': (255, 100, 0),
        'center': (0, 255, 0),
        'right': (0, 100, 255)
    }
    
    try:
        for lane_class, lane_dict in all_lanes.items():
            lane = lane_dict['lane_data']
            ploty_lane = lane['ploty']
            left_fitx_lane = lane['left_fitx']
            right_fitx_lane = lane['right_fitx']
            color = lane_colors.get(lane_class, (100, 100, 100))
            
            try:
                warped_h, warped_w = binary_warped.shape
                
                left_x_orig = ploty_lane
                left_y_orig = warped_w - left_fitx_lane
                right_x_orig = ploty_lane
                right_y_orig = warped_w - right_fitx_lane
                
                left_pts_unrot = np.array([np.transpose(np.vstack([left_x_orig, left_y_orig]))], dtype=np.float32)
                right_pts_unrot = np.array([np.transpose(np.vstack([right_x_orig, right_y_orig]))], dtype=np.float32)
                
                left_pts_orig = cv2.perspectiveTransform(left_pts_unrot, Minv)
                right_pts_orig = cv2.perspectiveTransform(right_pts_unrot, Minv)
                
                cv2.polylines(result, np.int32([left_pts_orig]), False, color, 3)
                cv2.polylines(result, np.int32([right_pts_orig]), False, color, 3)
                
                lane_bottom_x = int((left_pts_orig[-1][0][0] + right_pts_orig[-1][0][0]) / 2)
                lane_bottom_y = int((left_pts_orig[-1][0][1] + right_pts_orig[-1][0][1]) / 2)
                
                label_text = f"{lane_class.upper()}"
                if current_lane_data and lane_class == current_lane_data['lane_class']:
                    label_text += " (CURRENT)"
                
                cv2.putText(result, label_text, (lane_bottom_x - 40, lane_bottom_y + 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
            except Exception as label_err:
                print(f"Lane label error for {lane_class}: {label_err}")
        
        return result
        
    except Exception as e:
        print(f"Error in draw_multi_lane_overlay: {e}")
        return original_image


def create_mask_overlay(img, mask, alpha=0.4, color=(0, 255, 0)):
    """
    Create an overlay of a binary mask on the original image.
    
    Args:
        img: The original image (BGR)
        mask: Binary mask (0s and 1s)
        alpha: Transparency of the overlay (0.0 to 1.0)
        color: Color of the mask overlay (BGR tuple)
    
    Returns:
        Image with mask overlay
    """
    try:
        if img.dtype != np.uint8:
            img = img.astype(np.uint8)
            
        if mask.shape[:2] != img.shape[:2]:
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]))
        
        if mask.max() > 1:
            mask = (mask > 0).astype(np.uint8)
        
        colored_mask = np.zeros_like(img)
        colored_mask[mask > 0] = color
        
        overlay = img.copy()
        mask_bool = mask > 0
        
        for c in range(3):
            overlay[..., c] = np.where(
                mask_bool,
                (1 - alpha) * overlay[..., c] + alpha * color[c],
                overlay[..., c]
            )
        
        result = overlay.astype(np.uint8)
        
        return result
        
    except Exception as e:
        print(f"Error in create_mask_overlay: {e}")
        return img
