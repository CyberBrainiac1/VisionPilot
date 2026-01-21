import logging
import numpy as np
from aggregator import PerceptionAggregator, AggregationResult

logger = logging.getLogger(__name__)


class PerceptionClient:
    """
    Wrapper around PerceptionAggregator for convenient use in BeamNG simulation.
    
    This handles:
    - Aggregator initialization and health checks
    - Frame processing with fallback values
    - Result extraction and validation
    """
    
    def __init__(self, host='localhost', service_ports=None, timeout=2.0, auto_health_check=True):
        """
        Initialize perception client.
        
        Args:
            host: Hostname where services are running
            service_ports: Custom port mapping (if not using defaults)
            timeout: Request timeout per service
            auto_health_check: Check service health on startup
        """
        if service_ports is None:
            service_ports = {
                'lane_detection': 4777,
                'object_detection': 5777,
                'traffic_light_detection': 6777,
                'sign_detection': 7777,
                'sign_classification': 8777
            }
        
        service_config = {
            name: f'http://{host}:{port}'
            for name, port in service_ports.items()
        }
        
        self.aggregator = PerceptionAggregator(
            service_config=service_config,
            timeout=timeout
        )
        
        if auto_health_check:
            health = self.aggregator.health_check()
            if not all(health.values()):
                logger.warning("Not all services are healthy!")
                logger.warning(f"Service status: {health}")
    
    def process_frame(self, frame, speed_kph, timestamp_ns, vehicle_pos=None, vehicle_direction=None):
        """
        Process a frame from the camera sensor.
        
        Args:
            frame: Camera frame (numpy array)
            speed_kph: Vehicle speed
            timestamp_ns: Timestamp in nanoseconds
            vehicle_pos: Optional vehicle position
            vehicle_direction: Optional vehicle direction
        
        Returns:
            AggregationResult with all perception data
        """
        return self.aggregator.process_frame(
            frame=frame,
            speed_kph=speed_kph,
            timestamp_ns=timestamp_ns,
            vehicle_pos=vehicle_pos,
            vehicle_direction=vehicle_direction
        )
    
    def extract_lane_detection(self, result):
        """
        Extract lane detection results from aggregation result.
        
        Args:
            result: AggregationResult from process_frame
        
        Returns:
            Dict with lane detection metrics or fallback values
        """
        lane_result = result.results.get('lane_detection')
        
        if lane_result is None:
            logger.warning("Lane detection service returned None")
            return {
                'confidence': 0.0,
                'deviation': 0.0,
                'lane_center': 0.0,
                'vehicle_center': 0.0,
                'left_curvature': 0.0,
                'right_curvature': 0.0
            }
        
        # Extract metrics from service response
        metrics = lane_result.get('metrics', {})
        return {
            'confidence': float(metrics.get('confidence', 0.0)),
            'deviation': float(metrics.get('deviation', 0.0)),
            'lane_center': float(metrics.get('lane_center', 0.0)),
            'vehicle_center': float(metrics.get('vehicle_center', 0.0)),
            'left_curvature': float(metrics.get('left_curvature', 0.0)),
            'right_curvature': float(metrics.get('right_curvature', 0.0))
        }
    
    def extract_object_detection(self, result):
        """
        Extract object detection results.
        
        Args:
            result: AggregationResult from process_frame
        
        Returns:
            List of detections or empty list if failed
        """
        obj_result = result.results.get('object_detection')
        
        if obj_result is None:
            logger.warning("Object detection service returned None")
            return []
        
        return obj_result.get('detections', [])
    
    def extract_traffic_light_detection(self, result):
        """
        Extract traffic light detection results.
        
        Args:
            result: AggregationResult from process_frame
        
        Returns:
            List of traffic light detections or empty list if failed
        """
        tl_result = result.results.get('traffic_light_detection')
        
        if tl_result is None:
            logger.warning("Traffic light detection service returned None")
            return []
        
        return tl_result.get('detections', [])
    
    def extract_sign_detection(self, result):
        """
        Extract sign detection results.
        
        Args:
            result: AggregationResult from process_frame
        
        Returns:
            List of sign detections or empty list if failed
        """
        sign_det_result = result.results.get('sign_detection')
        
        if sign_det_result is None:
            logger.warning("Sign detection service returned None")
            return []
        
        return sign_det_result.get('detections', [])
    
    def extract_sign_classification(self, result):
        """
        Extract sign classification results.
        
        Args:
            result: AggregationResult from process_frame
        
        Returns:
            List of sign classifications or empty list if failed
        """
        sign_cls_result = result.results.get('sign_classification')
        
        if sign_cls_result is None:
            logger.warning("Sign classification service returned None")
            return []
        
        return sign_cls_result.get('classifications', [])
    
    def shutdown(self):
        """Shutdown the aggregator gracefully."""
        self.aggregator.shutdown()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
