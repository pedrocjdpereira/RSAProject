FROM python:3.10-slim

ENV FLASK_APP=main.py

ENV FLASK_RUN_HOST=0.0.0.0

RUN apt-get update && apt-get install -y \
    gcc \
    musl-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    qtbase5-dev \
    qtdeclarative5-dev \
    qttools5-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install requests flask redis paho-mqtt torch torchvision numpy pandas mediapipe opencv-python ultralytics

COPY src /src

EXPOSE 5000

COPY . .

WORKDIR /src

CMD ["python3", "-u", "main.py"]