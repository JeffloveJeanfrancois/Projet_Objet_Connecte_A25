import json
import time
import paho.mqtt.client as mqtt

class MqttLogger:

    def __init__(self, broker="10.4.1.113", port=1883, sujet="LecteurRFID/log"):
        self.sujet = sujet
        self.client = mqtt.Client()
        self.client.connect(broker, port, 60)

    def envoyer(self, date, type_carte, uid):
        payload = json.dumps({
            "date": date,
            "type": type_carte,
            "uid": uid
        })
        topic = f"{self.sujet}/{int(time.time())}"
        self.client.publish(topic, payload, qos=1)
