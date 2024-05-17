FROM arm64v8/python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    musl-dev \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    qtbase5-dev \
    qtdeclarative5-dev \
    qttools5-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install requests flask redis paho-mqtt torch torchvision numpy pandas mediapipe opencv-python ultralytics

WORKDIR /src

COPY /src .

RUN git clone https://github.com/ultralytics/yolov5.git 

COPY yolov5s.pt yolov5/

COPY peopleSitting_example1.mp4 .

EXPOSE 8001

ENV FLASK_APP=main.py

ENV FLASK_RUN_HOST=0.0.0.0

CMD ["python3", "-u", "main.py"]