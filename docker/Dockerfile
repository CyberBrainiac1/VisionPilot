FROM nvidia/cuda:12.2.0-cudnn8-runtime-ubuntu22.04

# dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-opencv git libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# working dir
WORKDIR /app

# copy src code/config/services
COPY src /app/src
COPY config /app/config
COPY services /app/services
COPY requirements.txt /app/

# install python dependencies
RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

# create model directories for volume mounts
RUN mkdir -p /app/models/scnn_lane_detection && \
    mkdir -p /app/models/object_detection && \
    mkdir -p /app/models/traffic_light && \
    mkdir -p /app/models/traffic_sign

# foxglove/model ports
EXPOSE 8765 4777 5777 6777 7777 8777