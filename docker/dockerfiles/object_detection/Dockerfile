FROM visionpilot-base

COPY src/perception/object_detection /app/src/perception/object_detection
COPY models/object_detection/object_detection.pth /app/models/object_detection/object_detection.pth
COPY services/object_detection_service.py /app/services/object_detection_service.py

ENV MODEL_PATH=/app/models/object_detection/object_detection.pth
ENV PYTHONUNBUFFERED=1

CMD ["python3", "/app/services/object_detection_service.py"]