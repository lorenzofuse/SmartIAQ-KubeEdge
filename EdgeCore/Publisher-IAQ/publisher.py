import pandas as pd
import time
import paho.mqtt.client as mqtt
from datetime import datetime
import os
import json
import base64
#librerie per crittografia, derivazioni chiavi simmetriche HKDF, AES
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


LOG_PATH = "/logs/iaq_pub.log"
DELAY = 1
#VARIA LA ZONA ASSEGNATA A SECONDA DELLA VM
SENSORS = ["Meeting1", "Meeting2", "Meeting3", "Meeting4"]
ZONE = "zone1"
SENDER = "edge2"
BROKER_IP = "192.168.9.128"

#carica la chiave privata ECC per la VM corrente, il file deve essere presente nella cartella kubeedge_microservices/app
with open("/app/ecc_private_edge2.pem", "rb") as f:
    priv_edge = serialization.load_pem_private_key(f.read(), None)
    
#carica la chiave pubblica ECC del cloud, il file deve essere presente nella cartella kubeedge_microservices/app
#questa chiave è condivisa tra tutti i nodi edge
with open("/app/ecc_public_cloud.pem", "rb") as f:
    pub_cloud = serialization.load_pem_public_key(f.read())

#inizializza il client MQTT e si connette al broker
client = mqtt.Client()
client.connect(BROKER_IP, 1883)

#carica i dati da file Excel, li unisce e mantengo la colonna Date come riferimento
df = pd.merge(
    pd.read_excel("CO2_Adeunis.xlsx")[["Date"] + SENSORS],
    pd.read_excel("temperatures_Adeunis.xlsx")[["Date"] + SENSORS],
    on="Date", suffixes=('_co2', '_temp')
)


print(f"Inizio simulazione con {len(df)} righe per zona {ZONE}...")

#funzione per crittografare e firmare i messaggi
def encrypt_and_sign(message: str) -> str:
    #genereazione chiave effimera (valida solo per questa sessione)
    eph = ec.generate_private_key(ec.SECP384R1())
    #deriva dal segreto condiviso tra chiave effimera e chiave pubblica del cloud tramite ECDH
    shared = eph.exchange(ec.ECDH(), pub_cloud)
    #HDKF per derivare la chiave AES simmetrica a 256 bit
    aes_key = HKDF(hashes.SHA256(), 32, None, b'handshake').derive(shared)
    #cifra il messaggio con AES in modalità CFB (Chiper Feedback con IV random)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
    encrypted = cipher.encryptor().update(message.encode())
    
    #firma il messaggio cifrato con la chiave privata ECC, usando ECDSA
    signature = priv_edge.sign(encrypted, ec.ECDSA(hashes.SHA256()))

    #payload JSON con i dati crittografati, firma e chiave pubblica effimera
    return json.dumps({
        "ciphertext": base64.b64encode(iv + encrypted).decode(),
        "signature": base64.b64encode(signature).decode(),
        "ephemeral_pubkey": eph.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode(),
        "sender": SENDER
    })

#loop per ogni riga dei due file excel uniti, lo cifra, pubblica i dati su MQTT e file log 
#tail -f /var/log/mqtt/iaq_pub.log
for idx, row in df.iterrows():
    timestamp = row["Date"]
    print(f"[{idx+1}/{len(df)}] {timestamp} → pubblicazione per zona {ZONE}")

    for sensor in SENSORS:
        topic = f"iaq/{ZONE}/{sensor.lower()}"
        co2 = row.get(f"{sensor}_co2")
        temp = row.get(f"{sensor}_temp")

        if pd.notna(co2):
            msg = f"{datetime.now()}, {timestamp}, CO2: {co2:.2f} ppm"
            encrypted = encrypt_and_sign(msg)
            client.publish(topic, encrypted)
            with open(LOG_PATH, "a") as log_file:
                log_file.write(f"{encrypted}\n")

        if pd.notna(temp):
            msg = f"{datetime.now()}, {timestamp}, TEMP: {temp:.2f} °C"
            encrypted = encrypt_and_sign(msg)
            client.publish(topic, encrypted)
            with open(LOG_PATH, "a") as log_file:
                log_file.write(f"{encrypted}\n")

    time.sleep(DELAY)

print("Simulazione completata.")
client.disconnect()
