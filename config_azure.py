import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERTFILE = os.path.join(BASE_DIR, "..", "certs", "client-subscriber.pem")
KEYFILE  = os.path.join(BASE_DIR, "..", "certs", "client-subscriber.key")

CONFIG = {
    "broker": "broker-mqtt.canadaeast-1.ts.eventgrid.azure.net",
    "port": 8883,

    # Authentication Name (Event Grid → "client-publisher")
    "username": "client-publisher",

    # Certificats mTLS
    "cert_file": CERTFILE,
    "key_file": KEYFILE,

    # Espaces de topics
    "topics": {
        "log": "LecteurRFID/log"
    }
}
