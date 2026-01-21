FROM visionpilot-base

COPY src/perception/traffic_light_detection /app/src/perception/traffic_light_detection
COPY models/traffic_light/traffic_light.pth /app/models/traffic_light/traffic_light.pth
COPY services/traffic_light_detection_service.py /app/services/traffic_light_detection_service.py

ENV MODEL_PATH=/app/models/traffic_light/traffic_light.pth
ENV PYTHONUNBUFFERED=1

CMD ["python3", "/app/services/traffic_light_detection_service.py"]
