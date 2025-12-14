import sys
import os
import yaml
import numpy as np
import math
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from beamngpy import BeamNGpy, Scenario, Vehicle
from beamngpy.sensors import Radar


def load_radar_config():
    config_path = 'beamng_sim/config/perception.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['perception']['radar']


def filter_radar(raw_points, radar_cfg):
    # Handle different input types
    if raw_points is None or (isinstance(raw_points, np.ndarray) and len(raw_points) == 0):
        return []
    
    # Keep as numpy array for efficiency, don't convert to list
    if isinstance(raw_points, np.ndarray) and len(raw_points) == 0:
        return []
    
    filtered_points = []
    filtering_cfg = radar_cfg['radar_filtering']
    
    # Debug: print first point structure (only once)
    debug_printed = False

    for i, point in enumerate(raw_points):
        try:
            # Unpack 7 values: range, doppler_vel, azimuth, elevation, rcs, snr_raw, quality
            range_dist = float(point[0])
            doppler_vel = float(point[1])
            azimuth_angle = float(point[2])
            elevation_angle = float(point[3])
            rcs = float(point[4])
            snr_raw = float(point[5])  # This appears to be very large
            quality = float(point[6])  # Quality metric 0-1
            
            if not debug_printed:
                print(f"Point structure - range:{range_dist:.2f}, doppler:{doppler_vel:.4f}, az:{azimuth_angle:.4f}, el:{elevation_angle:.4f}, rcs:{rcs:.1f}, snr:{snr_raw:.2e}, quality:{quality:.4f}")
                debug_printed = True

            # Use quality metric instead of SNR for filtering (0-1 range makes more sense)
            within_range = (range_dist <= filtering_cfg['max_range'] and range_dist >= filtering_cfg['min_range'])
            strong_signal = (quality >= 0.5)  # Quality threshold instead of SNR
            elevation = (elevation_angle <= filtering_cfg['max_elevation'] and elevation_angle >= filtering_cfg['min_elevation'])
            azimuth = (azimuth_angle <= filtering_cfg['max_azumith'] and azimuth_angle >= filtering_cfg['min_azumith'])

            if within_range and strong_signal and elevation and azimuth:
                # Store as tuple with 6 values (drop the huge SNR value)
                filtered_points.append((range_dist, doppler_vel, azimuth_angle, elevation_angle, rcs, quality))
                
        except (ValueError, TypeError, IndexError) as e:
            # Skip malformed points
            continue

    print(f"Filtered {len(filtered_points)} points from {len(raw_points)} raw points")
    return filtered_points


def convert_to_xyz(points):
    converted_points = []
    for point in points:
        try:
            # Unpack 6 values: range, doppler_vel, azimuth, elevation, rcs, quality
            range_dist, doppler_vel, azimuth_angle, elevation_angle, rcs, quality = point

            azimuth_angle = np.deg2rad(azimuth_angle)
            elevation_angle = np.deg2rad(elevation_angle)

            x = range_dist * np.cos(elevation_angle) * np.cos(azimuth_angle)
            y = range_dist * np.cos(elevation_angle) * np.sin(azimuth_angle)
            z = range_dist * np.sin(elevation_angle)

            # Store: x, y, z, doppler_vel, rcs, quality
            converted_points.append((x, y, z, doppler_vel, rcs, quality))
        except (ValueError, TypeError, IndexError):
            # Skip malformed points
            continue

    return converted_points


def calculate_aeb(converted_points, speed_kph, radar_cfg):
    if not converted_points or len(converted_points) == 0:
        return {
            'ttc': float('inf'),
            'closest_distance': None,
            'closest_velocity': None
        }
    
    min_dist = radar_cfg['aeb']['min_distance']
    closest_point = None

    try:
        for point in converted_points:
            try:
                # Unpack: x, y, z, doppler_vel, rcs, quality
                x, y, z, doppler_vel, rcs, quality = point
                distance = np.sqrt(x**2 + y**2 + z**2)
                if distance < min_dist:
                    min_dist = distance
                    closest_point = point
            except (ValueError, TypeError, IndexError):
                # Skip malformed points
                continue

        if closest_point is not None:
            x, y, z, doppler_vel, rcs, quality = closest_point
            ego_speed_mps = speed_kph / 3.6
            relative_velocity = ego_speed_mps - doppler_vel
            
            if relative_velocity > 0:
                ttc = min_dist / relative_velocity
            else:
                ttc = float('inf')
                
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
    except Exception as e:
        print(f"Error in calculate_aeb: {e}")
        return {
            'ttc': float('inf'),
            'closest_distance': None,
            'closest_velocity': None
        }

def yaw_to_quat(yaw_deg):
    """Convert yaw angle in degrees to quaternion."""
    yaw = math.radians(yaw_deg)
    w = math.cos(yaw / 2)
    z = math.sin(yaw / 2)
    return (0.0, 0.0, z, w)

def main():
    bng = BeamNGpy('localhost', 64256)
    bng.open(launch=True)

    scenario = Scenario('west_coast_usa', 'highway')
    vehicle = Vehicle('ego_vehicle', model='etk800', license='AEB TEST')

    rot = yaw_to_quat(-135.678)

    scenario.add_vehicle(vehicle, pos=(-287.21, 73.609, 112.363), rot_quat=rot)
    scenario.make(bng)
    bng.settings.set_deterministic(60)
    bng.scenario.load(scenario)
    bng.ui.hide_hud()
    bng.scenario.start()

    radar_front = Radar(
        'radar_front',
        bng,
        vehicle,
        requested_update_time=0.05,
        pos=(0, -3.5, 0.5),
        dir=(0, -1, 0),
        up=(0, 0, 1),
        size=(200, 200),
        near_far_planes=(0.1, 200),
        field_of_view_y=18,
        range_min=0.5,
        range_max=150.0,
        vel_min=-40,
        vel_max=40,
        range_bins=128,
        azimuth_bins=64,
        vel_bins=32,
        half_angle_deg=9,
        is_visualised=True
    )

    radar_cfg = load_radar_config()

    print("Spawning traffic")
    bng.traffic.spawn(max_amount=5, police_ratio=0.0, extra_amount=0, parked_amount=0)

    print("Waiting for radar to initialize...")
    time.sleep(2)
    
    # Test radar polling
    print("Testing radar poll...")
    for i in range(5):
        test_data = radar_front.poll()
        if test_data is not None:
            print(f"Test poll {i+1}: type={type(test_data)}, shape={test_data.shape if isinstance(test_data, np.ndarray) else 'N/A'}, len={len(test_data) if hasattr(test_data, '__len__') else 'N/A'}")
            if isinstance(test_data, np.ndarray) and len(test_data) > 0:
                print(f"  First point: {test_data[0]}")
                print(f"  Data dtype: {test_data.dtype}")
        else:
            print(f"Test poll {i+1}: None")
        time.sleep(0.1)

    manual_throttle = 0.50
    frame_count = 0

    try:
        while True:
            try:
                bng.control.step(10)

                vehicle.poll_sensors()
                state = vehicle.state

                speed_mps = np.linalg.norm([state['vel'][0], state['vel'][1], state['vel'][2]])
                speed_kph = speed_mps * 3.6

                radar_data = radar_front.poll()
                
                # Debug: Print radar data structure
                if radar_data is None:
                    print("WARNING: radar_data is None")
                    raw_points = []
                elif isinstance(radar_data, np.ndarray):
                    print(f"Radar is numpy array, shape: {radar_data.shape}, dtype: {radar_data.dtype}")
                    # The numpy array IS the point cloud
                    raw_points = radar_data if len(radar_data) > 0 else []
                elif isinstance(radar_data, dict):
                    print(f"Radar data keys: {radar_data.keys()}")
                    if 'point_cloud' in radar_data:
                        raw_points = radar_data['point_cloud']
                    else:
                        # Try other possible keys
                        raw_points = radar_data.get('points', radar_data.get('readings', []))
                else:
                    print(f"Radar data type: {type(radar_data)}")
                    raw_points = []
                
                filtered_points = filter_radar(raw_points, radar_cfg)
                converted_points = convert_to_xyz(filtered_points)
                
                # Print point statistics
                print(f"Raw points: {len(raw_points)}, Filtered: {len(filtered_points)}, Converted: {len(converted_points)}")

                aeb_result = calculate_aeb(converted_points, speed_kph, radar_cfg)
                ttc = aeb_result.get('ttc', float('inf'))
                closest_distance = aeb_result.get('closest_distance', None)

                if ttc <= 0.5:
                    print(f"EMERGENCY BRAKING: TTC {ttc:.2f}s, Distance {closest_distance:.2f}m")
                    throttle = 0.0
                    brake = 1.0
                elif ttc <= 1.5:
                    print(f"HARD BRAKING: TTC {ttc:.2f}s, Distance {closest_distance:.2f}m")
                    throttle = 0.0
                    brake = 0.6
                elif ttc <= 3.0:
                    print(f"MEDIUM BRAKING: TTC {ttc:.2f}s, Distance {closest_distance:.2f}m")
                    throttle = 0.0
                    brake = 0.4
                elif ttc <= 5.0:
                    print(f"GENTLE BRAKING: TTC {ttc:.2f}s, Distance {closest_distance:.2f}m")
                    throttle = manual_throttle * 0.3
                    brake = 0.1
                elif ttc < float('inf'):
                    print(f"WARNING: TTC {ttc:.2f}s, Distance {closest_distance:.2f}m")
                    throttle = manual_throttle * 0.5
                    brake = 0.0
                else:
                    throttle = manual_throttle
                    brake = 0.0

                # Ensure values are valid floats and in valid range
                throttle = float(np.clip(throttle, 0.0, 1.0))
                brake = float(np.clip(brake, 0.0, 1.0))
                
                try:
                    vehicle.control(throttle=throttle, brake=brake, steering=0.0)
                    time.sleep(0.01)  # Small delay after control
                except Exception as control_e:
                    print(f"Control error (continuing): {control_e}")
                    time.sleep(0.1)

                print(f"Speed: {speed_kph:.1f} km/h | TTC: {ttc:.2f}s | Points: {len(converted_points)} | Throttle: {throttle:.2f} | Brake: {brake:.2f}")
                frame_count += 1
                
            except KeyboardInterrupt:
                print("Test stopped by user")
                break
            except Exception as e:
                print(f"Error in loop: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                # Try to continue instead of breaking on errors
                time.sleep(0.5)

    except KeyboardInterrupt:
        print("Test Stopped")
    finally:
        bng.close()


if __name__ == '__main__':
    main()
