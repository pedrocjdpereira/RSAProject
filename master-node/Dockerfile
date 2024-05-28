FROM arm64v8/python:3.10-slim 
# para localhost - FROM python:3.10-slim 

RUN apt-get update

RUN apt-get install -y \
    gcc \ 
    musl-dev \
    sudo \
    batctl \
    net-tools

RUN pip install --upgrade pip

RUN pip install flask redis paho-mqtt

WORKDIR /src

COPY /src .

EXPOSE 5000

ENV FLASK_APP=main.py

ENV FLASK_RUN_HOST=0.0.0.0

CMD ["python3", "-u", "main.py"]