#!/bin/bash

echo "Starting Docker services"
echo ""

DOCKER_DIR="$(dirname "$0")/../docker"
cd "$DOCKER_DIR" || exit 1

docker compose up -d

echo ""
echo "Waiting for services to initialize"
sleep 15

echo ""
echo "Checking service health"
echo ""

# Detect if running in WSL and set appropriate host
HOST="localhost"
if grep -qi microsoft /proc/version 2>/dev/null; then
    HOST="host.docker.internal"
fi

services=(
    "object_detection:5777"
    "traffic_light_detection:6777"
    "sign_detection:7777"
    "sign_classification:8777"
    "yolop:9777"
)

all_healthy=true

for service_port in "${services[@]}"; do
    service_name="${service_port%:*}"
    port="${service_port##*:}"
    
    if curl -f http://$HOST:$port/health >/dev/null 2>&1; then
        echo "$service_name ($HOST:$port)"
    else
        echo "$service_name ($HOST:$port) - FAILED"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo "All services healthy!"
    echo ""
    echo "Next step: Run './start_simulation.sh' to start BeamNG + Foxglove"
else
    echo "Some services failed to start"
    echo ""
    echo "Check logs: cd $DOCKER_DIR && docker compose logs -f"
    exit 1
fi