"""
get vehicle center through like         
lane_center = (left_bottom + right_bottom) / 2.0
        
        if original_image_width is not None:
            vehicle_center = original_image_width / 2.0
        else:
            vehicle_center = binary_warped.shape[1] / 2.0

Vehicle position = center x of warped image

For each detected lane:
  lane_left_x = lane['left_boundary_x']
  lane_right_x = lane['right_boundary_x']
  
  if vehicle_x >= lane_left_x AND vehicle_x <= lane_right_x:
    return lane['lane_id']  # Found current lane!

If no match found:
  return None (vehicle not in detected lanes, edge case)
"""


def get_current_lane(lanes, vehicle_center=None, image_width=None):
    """
    Determine which lane vehicle is in and classify all lanes.
    
    Returns:
        Dict with current lane info and classified lanes
    """
    if vehicle_center is None:
        vehicle_center = image_width / 2
    
    current_lane = None
    classified_lanes = {}
    
    for lane in lanes:
        left_boundary_x = lane['left_fitx'][-1]
        right_boundary_x = lane['right_fitx'][-1]
        lane_id = lane['lane_id']
        
        # Classify lane by position
        if lane_id == 0:
            lane_class = 'left'
        elif lane_id == 1:
            lane_class = 'center'
        elif lane_id == 2:
            lane_class = 'right'
        else:
            lane_class = f'lane_{lane_id}'
        
        classified_lanes[lane_class] = {
            'lane_id': lane_id,
            'lane_data': lane,
            'left_x': left_boundary_x,
            'right_x': right_boundary_x
        }
        
        if left_boundary_x <= vehicle_center <= right_boundary_x:
            position = (vehicle_center - left_boundary_x) / (right_boundary_x - left_boundary_x)
            current_lane = {
                'lane_id': lane_id,
                'lane_class': lane_class,
                'position_in_lane': position,
                'lane_data': lane
            }
    
    return {
        'current_lane': current_lane,
        'all_lanes': classified_lanes
    }