def process_frame(radar_front_sensor, radar_cfg, speed_kph):
    """
    Process radar data for AEB and ACC.
    Returns raw radar data for decision logic in main loop.
    """
    radar_data = radar_front_sensor.poll()
    filtered_data = filter_radar(radar_data, radar_cfg)

    # Calculate metrics (logic to be implemented)
    aeb_result = calculate_aeb(filtered_data, speed_kph, radar_cfg)
    acc_result = calculate_acc(filtered_data, speed_kph, radar_cfg)

    # Return combined result with raw data for beamng.py to make decisions
    return {
        'ttc': aeb_result.get('ttc', float('inf')),
        'closest_distance': aeb_result.get('closest_distance', None),
        'closest_velocity': aeb_result.get('closest_velocity', None),
        'filtered_points': filtered_data,
        'acc_adjustment': acc_result.get('throttle_adjustment', None)
    }


def calculate_aeb(filtered_points, speed_kph, radar_cfg):
    """
    Calculate AEB metrics (TTC, distance, velocity).
    Logic to be implemented.
    """
    converted_points = convert_to_xyz(filtered_points)
    return {
        'ttc': float('inf'),
        'closest_distance': None,
        'closest_velocity': None
    }


def calculate_acc(filtered_points, speed_kph, radar_cfg):
    """
    Calculate ACC metrics (throttle adjustment).
    Logic to be implemented.
    """
    return {
        'throttle_adjustment': None
    }


def convert_to_xyz(points):


def filter_radar(radar_data, radar_cfg):

    try:
        raw_points = radar_data['point_cloud']
    except KeyError:
        print("radar missing 'point_cloud' key")
        raw_points = []

    filtered_points = []

    for point in raw_points:
        range_dist, doppler_vel, azumith_angle, elevation_angle, rcs, snr = point

        within_range = (range_dist <= radar_cfg['max_distance'] and range_dist >= radar_cfg['min_distance'])
        strong_signal = (snr >= radar_cfg['min_snr'])
        elevation = (elevation_angle <= radar_cfg['max_elevation'] and elevation_angle >= radar_cfg['min_elevation'])
        azumith = (azumith_angle <= radar_cfg['max_azumith'] and azumith_angle >= radar_cfg['min_azumith'])

        if within_range and strong_signal and elevation and azumith:
            filtered_points.append(point)

    return filtered_points