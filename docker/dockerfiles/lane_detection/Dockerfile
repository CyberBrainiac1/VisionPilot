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

RUN mkdir -p /app/models/scnn_lane_detection

ENV MODEL_PATH=/models/scnn_lane_detection/scnn.pth
ENV PYTHONUNBUFFERED=1

CMD ["python3", "/app/services/lane_detection_service.py"]

