import sys
import numpy as np
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from aggregator import PerceptionAggregator


def test_health_check():
    service_config = {
        'lane_detection': 'http://localhost:4777',
        'object_detection': 'http://localhost:5777',
        'traffic_light_detection': 'http://localhost:6777',
        'sign_detection': 'http://localhost:7777',
        'sign_classification': 'http://localhost:8777'
    }
    
    aggregator = PerceptionAggregator(service_config, timeout=2.0)
    health = aggregator.health_check()
    
    print("Health Check:")
    for service, is_healthy in health.items():
        status = "OK" if is_healthy else "DOWN"
        print(f"  {service}: {status}")
    
    return all(health.values())


def test_process_frame():
    service_config = {
        'lane_detection': 'http://localhost:4777',
        'object_detection': 'http://localhost:5777',
        'traffic_light_detection': 'http://localhost:6777',
        'sign_detection': 'http://localhost:7777',
        'sign_classification': 'http://localhost:8777'
    }
    
    aggregator = PerceptionAggregator(service_config, timeout=2.0)
    test_frame = np.random.randint(0, 255, size=(720, 1280, 3), dtype=np.uint8)
    
    try:
        result = aggregator.process_frame(
            frame=test_frame,
            speed_kph=50.0,
            timestamp_ns=1234567890,
            vehicle_pos=(100.0, 50.0, 0.0),
            vehicle_direction=(1.0, 0.0, 0.0)
        )
        
        print(f"Frame Processing: {result.processing_time_ms:.1f}ms")
        for service, status in result.service_status.items():
            print(f"  {service}: {status}")
        
        return result.all_healthy
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_error_handling():
    service_config = {
        'lane_detection': 'http://localhost:4777',
        'object_detection': 'http://localhost:9999',
        'traffic_light_detection': 'http://localhost:6777',
        'sign_detection': 'http://localhost:7777',
        'sign_classification': 'http://localhost:8777'
    }
    
    aggregator = PerceptionAggregator(service_config, timeout=1.0)
    test_frame = np.random.randint(0, 255, size=(720, 1280, 3), dtype=np.uint8)
    
    try:
        result = aggregator.process_frame(
            frame=test_frame,
            speed_kph=50.0,
            timestamp_ns=1234567890
        )
        
        print(f"Partial Results: {result.processing_time_ms:.1f}ms")
        for service, status in result.service_status.items():
            print(f"  {service}: {status}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    print("Running aggregator tests...\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Process Frame", test_process_frame),
        ("Error Handling", test_error_handling)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}:")
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print("\nInterrupted")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            results[test_name] = False
    
    print("\n\nResults:")
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
