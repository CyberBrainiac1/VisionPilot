try:
    from .foxglove_bridge import FoxgloveBridge
    bridge = FoxgloveBridge()
except ImportError:
    bridge = None
    print("[VisionPilot] foxglove package not installed - Foxglove visualization disabled")
    print("             Install with: pip install foxglove-sdk  (optional)")
