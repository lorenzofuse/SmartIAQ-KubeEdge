FROM python:3.12-slim

WORKDIR /app

COPY vm-metrics-publisher.py .

RUN pip install --no-cache-dir paho-mqtt psutil

CMD ["python3", "vm-metrics-publisher.py"]
