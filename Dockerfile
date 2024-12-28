#FROM python:latest
FROM minizinc/minizinc:2.8.4

RUN apt-get update \
    && apt-get install -y python3 \
    && apt-get install -y python3 python3-pip

#set working directory for the container
WORKDIR /home

COPY . .

RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt
