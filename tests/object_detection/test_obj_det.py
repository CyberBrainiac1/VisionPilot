import sys
import os
import math
import time
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from beamngpy import BeamNGpy, Scenario, Vehicle
from beamngpy.sensors import Camera
from ultralytics import YOLO

from config.config import OBJECT_DETECTION_MODEL


def yaw_to_quat(yaw_deg):
    """Convert yaw angle in degrees to quaternion."""
    yaw = math.radians(yaw_deg)
    w = math.cos(yaw / 2)
    z = math.sin(yaw / 2)
    return (0.0, 0.0, z, w)


def main():
    beamng_home = os.environ.get('BEAMNG_HOME', '')
    if not beamng_home:
        raise RuntimeError(
            "BEAMNG_HOME environment variable is not set.\n"
            "Example: $env:BEAMNG_HOME = 'C:\\Users\\<you>\\BeamNG.tech.v0.37.6.0'"
        )
    bng = BeamNGpy('localhost', 64256, home=beamng_home)
    bng.open(launch=True)

    scenario = Scenario('west_coast_usa', 'highway')
    vehicle = Vehicle('ego_vehicle', model='etk800', license='OBJ DET TEST')

    rot = yaw_to_quat(-135.678)
    scenario.add_vehicle(vehicle, pos=(-287.21, 73.609, 112.363), rot_quat=rot)
    scenario.make(bng)
    bng.settings.set_deterministic(60)
    bng.scenario.load(scenario)
    bng.scenario.start()

    camera = Camera(
        'camera_front',
        bng,
        vehicle,
        requested_update_time=0.05,
        pos=(0, 0.3, 0.61),
        dir=(0, 1, 0),
        field_of_view_y=60,
        near_far_planes=(0.1, 500),
        resolution=(1920, 1080),
        is_streaming=False,
    )

    print("Loading YOLO object detection model...")
    model = YOLO(str(OBJECT_DETECTION_MODEL))
    print("Model loaded")

    print("Spawning traffic...")
    bng.traffic.spawn(max_amount=15, police_ratio=0.0, extra_amount=5, parked_amount=0)
    print("Traffic spawned: 15+ vehicles")

    print("Waiting for camera to initialize...")
    time.sleep(2)

    frame_count = 0
    
    try:
        while True:
            try:
                bng.control.step(5)
                
                images = camera.stream()
                img = np.array(images['colour'])
                
                results = model(img, conf=0.5)
                
                annotated_frame = results[0].plot()
                
                cv2.imshow('Object Detection', annotated_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Exiting...")
                    break
                
                frame_count += 1
                
                if frame_count % 30 == 0:
                    print(f"Frame {frame_count}")
                
            except KeyboardInterrupt:
                print("Interrupted by user")
                break
            except Exception as e:
                print(f"Error in loop: {type(e).__name__}: {e}")
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("Test stopped")
    finally:
        cv2.destroyAllWindows()
        bng.close()


if __name__ == '__main__':
    main()
