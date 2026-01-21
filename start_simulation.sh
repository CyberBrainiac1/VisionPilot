#!/bin/bash

cd "$(dirname "$0")"

python -c "
from simulation.foxglove_integration.bridge_instance import bridge
import sys

try:
    bridge.start_server()
    bridge.initialize_channels()
    print('Foxglove ready - ws://localhost:8765')
    import time
    time.sleep(2)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" &

FOXGLOVE_PID=$!

sleep 3

python simulation/beamng.py

kill $FOXGLOVE_PID 2>/dev/null
wait $FOXGLOVE_PID 2>/dev/null
