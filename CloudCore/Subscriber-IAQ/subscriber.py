import paho.mqtt.client as mqtt
import psycopg2
import csv
import json
import base64
from datetime import datetime
#librerie per crittografia, derivazioni chiavi simmetriche HKDF, AES
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

LOG_FILE = "/app/logs/iaq_log.csv"

# Connessione al database PostgreSQL
conn = psycopg2.connect(
    dbname="iaq_db",
    user="iaq_user",
    password="iaq_pass",
    host="localhost"
)

#crea un cursore per eseguire le query
cursor = conn.cursor()
#svuota la tabella per evitare incongruenze con Grafana
cursor.execute("TRUNCATE TABLE iaq_schema.iaq_data;")
conn.commit()
print("Tabella svuotata all'avvio.")

#carica la chiave privata ECC del cloud, il file deve essere presente nella cartella kubeedge_microservices/app
with open("/app/ecc_private_cloud.pem", "rb") as f:
    priv_cloud = serialization.load_pem_private_key(f.read(), None)

pub_keys = {
    "edge": serialization.load_pem_public_key(open("/app/ecc_public_edge.pem", "rb").read()),
    "edge2": serialization.load_pem_public_key(open("/app/ecc_public_edge2.pem", "rb").read()),
    "edge3": serialization.load_pem_public_key(open("/app/ecc_public_edge3.pem", "rb").read())
}

#funziona per decifrare e verificare i messaggi
def decrypt_and_verify(payload_json):
    #decofica il JSON e i campi base64 contenenti il testo cifrato, la firma e il nodo mittente		
    obj = json.loads(payload_json)
    ciphertext = base64.b64decode(obj["ciphertext"])
    signature = base64.b64decode(obj["signature"])
    sender = obj.get("sender")

    if sender not in pub_keys:
        raise ValueError(f"Sender '{sender}' sconosciuto")

    #ricrea la chiave AES simmetrica con EDCH e HKDF
    ephemeral = serialization.load_pem_public_key(obj["ephemeral_pubkey"].encode())
    shared = priv_cloud.exchange(ec.ECDH(), ephemeral)
    aes_key = HKDF(hashes.SHA256(), 32, None, b'handshake').derive(shared)

    #decifra il messaggio con AES in modalità CFB
    #separa IV (16 byte) e testo cifrato (resto del payload)
    iv = ciphertext[:16]
    encrypted = ciphertext[16:]
    #crea il cifrario AES-CFB con la chiave e l'IV
    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
    #decifra il testo cifrato
    clear = cipher.decryptor().update(encrypted)
    #verifica la firma con la chiave pubblica del mittente
    pub_keys[sender].verify(signature, encrypted, ec.ECDSA(hashes.SHA256()))
    #converte i bytes decrittati in stringa
    return clear.decode()

#funzione per gestire i messaggi ricevuti
def on_message(client, userdata, msg):
    #timestamp arrivo del messaggio
    ts_arrivo = datetime.now()
    #esrtrae il topic dal messaggio
    topic = msg.topic

    try:
        #decifra e verifica il messaggio
        payload = decrypt_and_verify(msg.payload.decode())
        print(f"[SUB] {topic} → {payload}")

        #separa il messaggio ricevuto in 3 parti
        #ts_pub_raw: timestamp di pubblicazione,
        #ts_sensore_raw: timestamp del sensore,
        #misura: valore della misura
        ts_pub_raw, ts_sensore_raw, misura = payload.split(", ", 2)
        tipo, valore_raw = misura.split(": ")
        valore = float(valore_raw.split()[0])
        #converte i timestamp in oggetti datetime
        ts_pub = datetime.fromisoformat(ts_pub_raw)
        ts_sensore = ts_pub
        latenza = (ts_arrivo - ts_pub).total_seconds()
        #scrive i dati su file CSV e inserisce i dati dentro il db
        #tail -f /var/log/mqtt/iaq_log.csv
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([ts_arrivo, ts_pub, topic, ts_sensore, tipo.strip(), valore, latenza])

        cursor.execute("""
            INSERT INTO iaq_schema.iaq_data (
                ts_arrivo, topic, ts_sensore, tipo, valore, latenza_pub_sub
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (ts_arrivo, topic, ts_sensore, tipo.strip(), valore, latenza))
        conn.commit()

    except Exception as e:
        print(f"Errore parsing/decrittazione/firma: {e} – Messaggio grezzo: {msg.payload[:80]}")
        conn.rollback()

client = mqtt.Client()
client.on_message = on_message
client.connect("127.0.0.1", 1883)
client.subscribe("iaq/#")
print("Subscriber e DB - attivo")
client.loop_forever() #mantiene il client in ascolto permanente dei messaggi 

