import os
import sys
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

"""
Utility function for collecting lidar point cloud data, to later be used for processing
"""

def collect_lidar_data(beamng, lidar_data):
    
    if lidar_data is None:
        print("LiDAR data is None")
        return np.array([]).reshape(0, 3)
    
    readings_data = lidar_data
    
    point_cloud = readings_data.get("pointCloud", [])

    if isinstance(point_cloud, np.ndarray):
        return point_cloud
    if isinstance(point_cloud, list) and len(point_cloud) > 0:
        return np.array(point_cloud)
    return np.array([]).reshape(0, 3)