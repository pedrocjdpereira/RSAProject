FROM arm64v8/python:3.10-alpine

WORKDIR /src

ENV FLASK_APP=main.py

ENV FLASK_RUN_HOST=0.0.0.0

RUN apk add --no-cache gcc musl-dev linux-headers

RUN pip install --upgrade pip

COPY src /src

RUN pip install flask redis paho-mqtt

EXPOSE 5000

COPY . .

CMD ["python3", "-u", "main.py"]