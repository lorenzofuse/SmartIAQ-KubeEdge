import paho.mqtt.client as mqtt
import psutil
import socket
import time
import json

broker_address = "192.168.9.128" 
topic = f"vm/metrics/{socket.gethostname()}"

client = mqtt.Client()
client.connect(broker_address, 1883)

while True:
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()

    payload = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "hostname": socket.gethostname(),
        "cpu_percent": cpu,
        "ram_used_mb": ram.used // (1024 * 1024),
        "ram_total_mb": ram.total // (1024 * 1024),
        "disk_used_gb": round(disk.used / (1024**3), 2),
        "net_in_kbps": round(net.bytes_recv / 1024, 2),
        "net_out_kbps": round(net.bytes_sent / 1024, 2)
    }

    client.publish(topic, json.dumps(payload))
    time.sleep(10)
