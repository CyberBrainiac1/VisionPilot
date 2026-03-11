from math import cos, sin
import numpy as np

def process_frame(radar_front_sensor, radar_cfg, speed_kph):
    """
    Process radar data for AEB and ACC.
    Returns raw radar data for decision logic in main loop.
    """
    radar_points = radar_front_sensor.poll()
    if radar_points is None:
        print("Warning: Radar poll returned None")
        radar_points = {}
    filtered_points = filter_radar(radar_points, radar_cfg)

    converted_points = convert_to_xyz(filtered_points)

    # Calculate metrics (logic to be implemented)
    aeb_result = calculate_aeb(converted_points, speed_kph, radar_cfg)
    acc_result = calculate_acc(converted_points, speed_kph, radar_cfg)

    # Return combined result with raw data for beamng.py to make decisions
    return {
        'ttc': aeb_result.get('ttc', float('inf')),
        'closest_distance': aeb_result.get('closest_distance', None),
        'closest_velocity': aeb_result.get('closest_velocity', None),
        'converted_points': converted_points,
        'acc_adjustment': acc_result.get('throttle_adjustment', None)
    }


def calculate_aeb(converted_points, speed_kph, radar_cfg):
    """
    Calculate AEB metrics (TTC, distance, velocity).
    Logic to be implemented.

    TTC = Relative Distance / Relative Velocity
    Relative distance is the distance to the target
    Relative velocity is the difference between ego vehicle speed and target speed
    Relative velocity (Doppler velocity) is positive when the target is approaching, negative when receding.

    """
    min_dist = radar_cfg['aeb']['min_distance']
    closest_point = None

    for point in converted_points:
        x, y, z, doppler_vel, _, _ = point
        distance = np.sqrt(x**2 + y**2 + z**2) # Euclidean distance
        if distance < min_dist:
            min_dist = distance # Distance from ego vehicle to target
            closest_point = point
    if closest_point is not None:
        _, _, _, doppler_vel, _, _ = closest_point

        ego_speed_mps = speed_kph / 3.6
        relative_velocity = ego_speed_mps - doppler_vel

        ttc = min_dist / relative_velocity if relative_velocity > 0 else float('inf')
        return {
            'ttc': ttc,
            'closest_distance': min_dist,
            'closest_velocity': doppler_vel
        }
    else:
        return {
            'ttc': float('inf'),
            'closest_distance': None,
            'closest_velocity': None
        }

def calculate_acc(converted_points, speed_kph, radar_cfg):
    """
    Calculate ACC metrics (throttle adjustment).
    Logic to be implemented.
    """
    return {
        'throttle_adjustment': None
    }


def convert_to_xyz(points):
    converted_points = []
    for point in points:
        range_dist, doppler_vel, azimuth_angle, elevation_angle, rcs, snr = point

        azimuth_angle = np.deg2rad(azimuth_angle)
        elevation_angle = np.deg2rad(elevation_angle)

        x = range_dist * cos(elevation_angle) * cos(azimuth_angle)
        y = range_dist * cos(elevation_angle) * sin(azimuth_angle)
        z = range_dist * sin(elevation_angle)

        converted_points.append((x, y, z, doppler_vel, rcs, snr))

    return converted_points


def filter_radar(radar_data, radar_cfg):

    if radar_data is None:
        print("Warning: radar_data is None in filter_radar")
        return []

    try:
        raw_points = radar_data['point_cloud']
    except (KeyError, TypeError):
        print("radar missing 'point_cloud' key or radar_data is not dict-like")
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