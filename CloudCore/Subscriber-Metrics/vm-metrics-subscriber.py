import paho.mqtt.client as mqtt
import psycopg2
import json

#Connessione a PostgreSQL (sulla stessa VM CloudCore)
conn = psycopg2.connect(
    dbname="iaq_db",
    user="iaq_user",
    password="iaq_pass",
    host="localhost",
    port=5432
)
cursor = conn.cursor()

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        cursor.execute("""
            INSERT INTO iaq_schema.vm_metrics (
                timestamp, hostname, cpu_percent,
                ram_used_mb, ram_total_mb, disk_used_gb,
                net_in_kbps, net_out_kbps
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["timestamp"],
            data["hostname"],
            data["cpu_percent"],
            data["ram_used_mb"],
            data["ram_total_mb"],
            data["disk_used_gb"],
            data["net_in_kbps"],
            data["net_out_kbps"]
        ))
        conn.commit()

    except Exception as e:
        print("Errore nel salvataggio su DB:", e)

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.subscribe("vm/metrics/#")
client.on_message = on_message

print("Subscriber attivo su 'vm/metrics/#'")
client.loop_forever()