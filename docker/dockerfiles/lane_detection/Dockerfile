FROM visionpilot-base

COPY src/perception/lane_detection /app/src/perception/lane_detection
COPY models/lane_detection/scnn.pth /app/models/lane_detection/scnn.pth
COPY services/lane_detection_service.py /app/services/lane_detection_service.py

ENV MODEL_PATH=/app/models/lane_detection/scnn.pth
ENV PYTHONUNBUFFERED=1

CMD ["python3", "/app/services/lane_detection_service.py"]

