FROM nvidia/cuda:12.2.0-cudnn8-runtime-ubuntu22.04

# dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-opencv git libgl1-mesa-glx

# set working dir
WORKDIR /app

COPY . /app

# install packages and upgrade pip
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Foxglove websocket port
EXPOSE 8765

# TODO: change to script that runs, foxglove, beamng, and the containers
# CMD ["python3", "simulation/beamng.py"]