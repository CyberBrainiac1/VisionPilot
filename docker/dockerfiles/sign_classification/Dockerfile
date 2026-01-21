FROM visionpilot-base

COPY src/perception/sign_detection /app/src/perception/sign_detection
COPY models/traffic_sign/traffic_sign_classification.h5 /app/models/traffic_sign/traffic_sign_classification.h5
COPY services/sign_classification_service.py /app/services/sign_classification_service.py

ENV MODEL_PATH=/app/models/traffic_sign/traffic_sign_classification.h5
ENV PYTHONUNBUFFERED=1

CMD ["python3", "/app/services/sign_classification_service.py"]
