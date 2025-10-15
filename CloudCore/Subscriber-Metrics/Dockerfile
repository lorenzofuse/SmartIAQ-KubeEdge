FROM python:3.12-slim

WORKDIR /app

COPY vm-metrics-subscriber.py .

RUN pip install --no-cache-dir paho-mqtt psycopg2-binary

CMD ["python3", "vm-metrics-subscriber.py"]
