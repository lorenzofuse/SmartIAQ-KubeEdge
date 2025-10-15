FROM python:3.12-slim

WORKDIR /app


COPY app/ /app/


COPY app/ecc_private_cloud.pem /app/
COPY app/ecc_public_edge.pem /app/
COPY app/ecc_public_edge2.pem /app/
COPY app/ecc_public_edge3.pem /app/


RUN pip install --no-cache-dir paho-mqtt psycopg2-binary cryptography


RUN mkdir /app/logs

CMD ["python3", "/app/subscriber.py"]
