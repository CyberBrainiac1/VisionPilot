#!/bin/bash

echo "Starting VisionPilot"

# build services
docker compose build

# launch all docker containers
docker compose up -d

# wait for all services
echo "waiting for services to start"
sleep 10

# check health
for service in redis lane_detection sign_detection traffic_light_detection object_detection aggregator; do
    curl -f http://localhost:$([ "$service" = "aggregator" ] && echo 5000 || [ "$service" = "redis" ] && echo 6379 || echo 8001)/health 2>/dev/null && echo "✅ $service healthy" || echo "❌ $service failed"
done

echo ""
echo "Stack is running"
echo "Foxglove WebSocket: ws://localhost:8765"
echo "Aggregator API: http://localhost:5000"
echo ""
echo "docker compose down to stop"