FROM python:3.10-slim

WORKDIR /src

ENV FLASK_APP=main.py

ENV FLASK_RUN_HOST=0.0.0.0

RUN apt update

RUN apt install -y gcc musl-dev

RUN pip install --upgrade pip

RUN pip install flask redis paho-mqtt

COPY src /src

EXPOSE 5000

COPY . .

CMD ["python3", "-u", "main.py"]