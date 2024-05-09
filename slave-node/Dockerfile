FROM python:3.10-slim

WORKDIR /src

ENV FLASK_APP=main.py

ENV FLASK_RUN_HOST=0.0.0.0

RUN apt-get update && apt-get install gcc musl-dev ffmpeg libsm6 libxext6  -y

RUN pip install --upgrade pip

RUN pip install requests flask redis paho-mqtt torch torchvision numpy pandas mediapipe opencv-python

COPY src /src

EXPOSE 5000

COPY . .

CMD ["python3", "-u", "main.py"]