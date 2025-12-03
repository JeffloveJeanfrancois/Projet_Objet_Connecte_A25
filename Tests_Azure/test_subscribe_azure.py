import ssl
import time
import os
import paho.mqtt.client as mqtt

BROKER = "broker-mqtt.canadaeast-1.ts.eventgrid.azure.net"
PORT = 8883

USERNAME = "client-subscriber"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERTFILE = os.path.join(BASE_DIR, "..", "certs", "client-subscriber.pem")
KEYFILE  = os.path.join(BASE_DIR, "..", "certs", "client-subscriber.key")

TOPIC = "LecteurRFID/logs/#"


def on_connect(client, userdata, flags, rc): # Removed properties=None
    print(f"[CONNECT] RC={rc}")
    if rc == 0:
        print("✓ Subscriber connecté")
        # Subscribing now works because the Client Attribute is correctly set
        client.subscribe(TOPIC, qos=1)
        print(f"→ Souscription à {TOPIC}")
    else:
        print(f"✗ Échec connexion subscriber (RC={rc})")


def on_message(client, userdata, msg):
    print(f"📬 [MESSAGE] {msg.topic} → {msg.payload.decode()}")


client = mqtt.Client(
    client_id="python-subscriber-test",
    protocol=mqtt.MQTTv311
)


client.on_connect = on_connect
client.on_message = on_message

client.tls_set(
    ca_certs=None,
    certfile=CERTFILE,
    keyfile=KEYFILE,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

client.username_pw_set(username=USERNAME, password=None)

print("Connexion…")
client.connect(BROKER, PORT)
client.loop_start()

print("En attente de messages (Ctrl+C pour quitter)…")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Arrêt demandé.")

client.loop_stop()
client.disconnect()
print("Déconnexion subscriber.")