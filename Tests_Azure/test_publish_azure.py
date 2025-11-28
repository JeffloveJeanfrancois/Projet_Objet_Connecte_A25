#!/usr/bin/env python3
import ssl
import time
import paho.mqtt.client as mqtt
import os

BROKER = "broker-mqtt.canadaeast-1.ts.eventgrid.azure.net"
PORT = 8883

USERNAME = "client-publisher"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERTFILE = os.path.join(BASE_DIR, "..", "certs", "client-publisher.pem")
KEYFILE  = os.path.join(BASE_DIR, "..", "certs", "client-publisher.key")

TOPIC = "LecteurRFID/logs/test"
MESSAGE = "Message test depuis publisher_test.py"
connected_flag = False

def on_connect(client, userdata, flags, rc): # Removed properties=None
    global connected_flag
    print(f"[CONNECT] RC={rc}")
    if rc == 0:
        print("✓ Connexion réussie à Azure MQTT")
        connected_flag = True
    else:
        print(f"✗ Échec de connexion (RC={rc})")

def on_publish(client, userdata, mid):
    print(f"✅ [PUBLISH] Message publié et accusé de réception (mid={mid})")


client = mqtt.Client(
    client_id="python-publisher-test",
    protocol=mqtt.MQTTv311,
)

# client.properties = {"type": "publisher"} <-- REMOVED: This is now correctly set in Azure.

client.on_connect = on_connect
client.on_publish = on_publish

client.tls_set(
    ca_certs=None,
    certfile=CERTFILE,
    keyfile=KEYFILE,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

client.username_pw_set(username=USERNAME, password=None)

print("Connexion au broker...")
client.connect(BROKER, PORT)
client.loop_start()

# Wait for the connection to complete successfully
wait_start = time.monotonic()
while not connected_flag and (time.monotonic() - wait_start) < 5:
    time.sleep(0.1)

if connected_flag:
    print(f"\nPublication sur {TOPIC} ...")
    
    # Block until the publish operation completes and we get confirmation (QoS 1)
    info = client.publish(TOPIC, MESSAGE, qos=1)
    info.wait_for_publish() 
    
else:
    print("\nSkipping publish: Connection failed or timed out.")

client.loop_stop()
client.disconnect()
print("Déconnexion terminée.")