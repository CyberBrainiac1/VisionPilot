import sys
import os
import yaml
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from beamngpy import BeamNGpy, Scenario, Vehicle
from beamngpy.sensors import Radar


def load_radar_config():
    config_path = 'beamng_sim/config/perception.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['perception']['radar']


def filter_radar(radar_data, radar_cfg):
    try:
        raw_points = radar_data['point_cloud']
    except KeyError:
        print("radar missing 'point_cloud' key")
        raw_points = []

    filtered_points = []
    filtering_cfg = radar_cfg['radar_filtering']

    for point in raw_points:
        range_dist, doppler_vel, azimuth_angle, elevation_angle, rcs, snr = point

        within_range = (range_dist <= filtering_cfg['max_range'] and range_dist >= filtering_cfg['min_range'])
        strong_signal = (snr >= filtering_cfg['min_snr'])
        elevation = (elevation_angle <= filtering_cfg['max_elevation'] and elevation_angle >= filtering_cfg['min_elevation'])
        azimuth = (azimuth_angle <= filtering_cfg['max_azumith'] and azimuth_angle >= filtering_cfg['min_azumith'])

        if within_range and strong_signal and elevation and azimuth:
            filtered_points.append(point)

    return filtered_points


def convert_to_xyz(points):
    converted_points = []
    for point in points:
        range_dist, doppler_vel, azimuth_angle, elevation_angle, rcs, snr = point

        azimuth_angle = np.deg2rad(azimuth_angle)
        elevation_angle = np.deg2rad(elevation_angle)

        x = range_dist * np.cos(elevation_angle) * np.cos(azimuth_angle)
        y = range_dist * np.cos(elevation_angle) * np.sin(azimuth_angle)
        z = range_dist * np.sin(elevation_angle)

        converted_points.append((x, y, z, doppler_vel, rcs, snr))

    return converted_points


def calculate_aeb(converted_points, speed_kph, radar_cfg):
    min_dist = radar_cfg['aeb']['min_distance']
    closest_point = None

    for point in converted_points:
        x, y, z, doppler_vel, _, _ = point
        distance = np.sqrt(x**2 + y**2 + z**2)
        if distance < min_dist:
            min_dist = distance
            closest_point = point

    if closest_point is not None:
        _, _, _, doppler_vel, _, _ = closest_point
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


def setup_visualization():
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('X (Forward) [m]')
    ax.set_ylabel('Y (Left) [m]')
    ax.set_zlabel('Z (Up) [m]')
    ax.set_title('Radar Point Cloud - Filtered Points')
    ax.set_xlim(0, 100)
    ax.set_ylim(-50, 50)
    ax.set_zlim(-10, 10)
    return fig, ax


def update_visualization(ax, raw_points, filtered_points, converted_points):
    ax.clear()
    ax.set_xlabel('X (Forward) [m]')
    ax.set_ylabel('Y (Left) [m]')
    ax.set_zlabel('Z (Up) [m]')
    ax.set_title(f'Radar Points - Raw: {len(raw_points)}, Filtered: {len(filtered_points)}')
    ax.set_xlim(0, 100)
    ax.set_ylim(-50, 50)
    ax.set_zlim(-10, 10)

    if converted_points:
        x_coords = [p[0] for p in converted_points]
        y_coords = [p[1] for p in converted_points]
        z_coords = [p[2] for p in converted_points]
        doppler_vels = [p[3] for p in converted_points]
        
        scatter = ax.scatter(x_coords, y_coords, z_coords, c=doppler_vels, 
                           cmap='RdYlGn', s=50, alpha=0.6)
        plt.colorbar(scatter, ax=ax, label='Doppler Velocity [m/s]')

    ax.scatter([0], [0], [0], c='red', s=200, marker='^', label='Ego Vehicle')
    ax.legend()


def main():
    bng = BeamNGpy('localhost', 64256)
    bng.open(launch=True)

    scenario = Scenario('west_coast_usa', 'aeb_test')
    vehicle = Vehicle('ego_vehicle', model='etk800', license='AEB TEST')

    radar_front = Radar('radar_front', bng, vehicle, 
                       pos=(0.0, 0.0, 0.5), dir=(0, -1, 0),
                       up=(0, 0, 1), size=(200, 200),
                       field_of_view_y=70, near_far_planes=(0.1, 150),
                       range_roundness=-2.0, range_cutoff_sensitivity=0.0,
                       range_shape=0.23, range_focus=0.12, range_min_cutoff=0.5,
                       range_direct_max_cutoff=150.0)

    scenario.add_vehicle(vehicle, pos=(-717.87, 101.29, 118.675), rot_quat=(0, 0, 0.3826834, 0.9238795))
    scenario.make(bng)
    bng.settings.set_deterministic(60)
    bng.scenario.load(scenario)
    bng.ui.hide_hud()
    bng.scenario.start()

    radar_cfg = load_radar_config()

    print("Spawning traffic")
    bng.traffic.spawn(max_amount=5, police_ratio=0.0, extra_amount=0, parked_amount=0)

    fig, ax = setup_visualization()
    plt.ion()
    plt.show()

    manual_throttle = 0.15


    try:
        while True:
            bng.control.step(10)

            vehicle.poll_sensors()
            state = vehicle.state

            speed_mps = np.linalg.norm([state['vel'][0], state['vel'][1], state['vel'][2]])
            speed_kph = speed_mps * 3.6

            radar_data = radar_front.poll()
            raw_points = radar_data.get('point_cloud', [])
            filtered_points = filter_radar(radar_data, radar_cfg)
            converted_points = convert_to_xyz(filtered_points)

            aeb_result = calculate_aeb(converted_points, speed_kph, radar_cfg)
            ttc = aeb_result['ttc']
            closest_distance = aeb_result['closest_distance']

            if ttc <= 1.0:
                print(f"EMERGENCY BRAKING: TTC {ttc:.2f}s, Distance {closest_distance:.2f}m")
                throttle = 0.0
                brake = 1.0
            elif ttc <= 3.0:
                print(f"MEDIUM BRAKING: TTC {ttc:.2f}s, Distance {closest_distance:.2f}m")
                throttle = 0.0
                brake = 0.3
            elif ttc < float('inf'):
                print(f"WARNING: TTC {ttc:.2f}s, Distance {closest_distance:.2f}m")
                throttle = manual_throttle * 0.5
                brake = 0.0
            else:
                throttle = manual_throttle
                brake = 0.0

            vehicle.control(throttle=throttle, brake=brake, steering=0.0)

            update_visualization(ax, raw_points, filtered_points, converted_points)
            plt.pause(0.01)

            print(f"Speed: {speed_kph:.1f} km/h | TTC: {ttc:.2f}s | Points: {len(converted_points)} | Throttle: {throttle:.2f} | Brake: {brake:.2f}")

    except KeyboardInterrupt:
        print("Test Stopped")
    finally:
        bng.close()
        plt.close()


if __name__ == '__main__':
    main()
