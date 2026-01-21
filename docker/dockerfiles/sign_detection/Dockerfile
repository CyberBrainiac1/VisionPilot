FROM visionpilot-base

COPY src/perception/sign_detection /app/src/perception/sign_detection
COPY models/traffic_sign/traffic_sign_detection.pth /app/models/traffic_sign/traffic_sign_detection.pth
COPY services/sign_detection_service.py /app/services/sign_detection_service.py

ENV MODEL_PATH=/app/models/traffic_sign/traffic_sign_detection.pth
ENV PYTHONUNBUFFERED=1

CMD ["python3", "/app/services/sign_detection_service.py"]
