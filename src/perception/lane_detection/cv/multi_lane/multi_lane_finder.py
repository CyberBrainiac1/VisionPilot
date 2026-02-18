import numpy as np
from scipy.signal import find_peaks
import cv2 as cv

def find_lane_boundaries(histogram, num_peaks=4, min_distance=80, height_threshold=None):
    """
    Find lane boundaries using peajs in the histogram.

    args:
        histogram: 1D array representing the histogram of pixel intensities.
        num_peaks: Maximum number of peaks to identify (default is 4).
        min_distance: Minimum distance between peaks in pixels (default is 80).
        height_threshold: Minimum height of peaks to be considered valid (default is None, which means no threshold).

    returns:
        List of lane boundary positions (x-coordinates) in the image.
    

    """

    if height_threshold is None:
        height_threshold = 0.2 * np.max(histogram)
    
    peaks, properties = find_peaks(histogram, distance=min_distance, height=height_threshold)
    
    top_peaks = sorted(peaks, key=lambda x: histogram[x], reverse=True)[:num_peaks]
    lane_boundaries = sorted(top_peaks)

    return lane_boundaries

def sliding_window_search(binary_warped, start_x, histogram, num_windows=9, window_height=80, margin=100, minpix=50, debug_display=False):
    """
    Perform sliding window search to find lane pixels and fit polynomial.

    args:
        binary_warped: Warped binary image where lane lines are highlighted.
        histogram: 1D array representing the histogram of pixel intensities.
        num_windows: Number of sliding windows (default is 9).
        margin: Width of the windows +/- margin (default is 100).
        minpix: Minimum number of pixels found to recenter window (default is 50).
        debug_display: If True, display intermediate results for debugging (default is False).
    returns:
        ploty: Array of y-coordinates for plotting.
    """

    height, width = binary_warped.shape

    ploty = np.linspace(height -1, 0, height)

    nonzero = cv.findNonZero(binary_warped.astype(np.uint8))
    if nonzero is None:
        return None
    
    nonzero_y = nonzero[:, 0, 1]
    nonzero_x = nonzero[:, 0, 0]

    lane_x = []
    current_x = start_x

    for window in range(len(ploty) // window_height):
        window_y_low = height - (window + 1) * window_height
        window_y_high = height - window * window_height
        
        window_x_low = current_x - margin
        window_x_high = current_x + margin
        
        good_inds = (
            (nonzero_y >= window_y_low) &
            (nonzero_y < window_y_high) &
            (nonzero_x >= window_x_low) &
            (nonzero_x < window_x_high)
        )
        
        if np.sum(good_inds) > minpix:
            current_x = int(np.mean(nonzero_x[good_inds]))
        
        lane_x.append(current_x)
    
    lane_y_positions = [height - (i + 0.5) * window_height for i in range(len(lane_x))]
    
    try:
        fit = np.polyfit(lane_y_positions, lane_x, 2)
        fitx = np.poly1d(fit)(ploty)
    except:
        fitx = np.array([start_x] * len(ploty))
        fit = None
    
    return {
        'fitx': fitx,
        'fit': fit,
        'ploty': ploty,
        'x_positions': lane_x
    }


def detect_multiple_lanes(binary_warped, num_lanes=3):
    """
    Detect multiple lanes (current ± 1) from binary warped image.
    
    Detects 4 boundaries which create 3 lanes between them.
    Each lane has left_fitx (inner boundary) and right_fitx (outer boundary).
    
    Args:
        binary_warped: Binary warped perspective image
        num_lanes: Number of lanes to detect (default 3, creates 4 boundaries)
    
    Returns:
        List of lane data dicts with left_fitx and right_fitx, or None if detection fails
    """
    histogram = np.sum(binary_warped, axis=0)
    
    num_peaks = num_lanes + 1
    lane_boundaries = find_lane_boundaries(histogram, num_peaks=num_peaks)
    
    if lane_boundaries is None or len(lane_boundaries) < num_peaks:
        lane_boundaries = find_lane_boundaries(histogram, num_peaks=num_peaks, height_threshold=0.1 * np.max(histogram))
    
    if lane_boundaries is None or len(lane_boundaries) < num_peaks:
        return None
    
    boundary_fitx = []
    for boundary_x in lane_boundaries:
        result = sliding_window_search(binary_warped, start_x=boundary_x, histogram=histogram)
        
        if result is None:
            return None
        
        boundary_fitx.append(result)
    
    lanes = []
    for i in range(num_lanes):
        if i + 1 >= len(boundary_fitx):
            break
        lane_data = {
            'lane_id': i,
            'left_fitx': boundary_fitx[i]['fitx'],      # Left boundary
            'right_fitx': boundary_fitx[i + 1]['fitx'],  # Right boundary
            'left_fit': boundary_fitx[i]['fit'],
            'right_fit': boundary_fitx[i + 1]['fit'],
            'ploty': boundary_fitx[i]['ploty'],
            'left_boundary_x': lane_boundaries[i],
            'right_boundary_x': lane_boundaries[i + 1],
        }
        lanes.append(lane_data)
    
    return lanes if len(lanes) == num_lanes else None