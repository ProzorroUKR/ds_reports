FROM python:3.9.13-slim-buster
RUN apt-get update && apt-get install -y git gcc libssl-dev
WORKDIR /app
ADD requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app
RUN python3 -m venv .
RUN ./bin/pip install -e .
