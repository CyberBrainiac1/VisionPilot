FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip python3-opencv git libgl1-mesa-glx curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src /app/src
COPY services /app/services
COPY config /app/config
COPY requirements.txt /app/

RUN pip3 install --upgrade pip && \
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117 && \
    pip3 install -r requirements.txt

RUN mkdir -p /app/models/object_detection

ENV MODEL_PATH=/models/object_detection/object_detection.pt
ENV PYTHONUNBUFFERED=1

CMD ["python3", "/app/services/object_detection_service.py"]