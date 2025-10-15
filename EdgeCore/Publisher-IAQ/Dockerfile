FROM python:3.12-slim

WORKDIR /app


COPY app/ /app/


COPY app/ecc_private_edge2.pem /app/
COPY app/ecc_public_cloud.pem /app/


RUN pip install --no-cache-dir pandas paho-mqtt openpyxl cryptography


CMD ["python3", "/app/publisher.py"]
