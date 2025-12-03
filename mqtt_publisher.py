import json
import ssl
import paho.mqtt.client as mqtt


class MqttPublisher:
    def __init__(
        self,
        utiliser_mqtt: bool,
        broker: str,
        port: int,
        sujet_log: str,
        mqtt_username: str = None,
        mqtt_certfile: str = None,
        mqtt_keyfile: str = None,
    ):
        self.utiliser_mqtt = utiliser_mqtt
        self.broker = broker
        self.port = port
        self.sujet_log = sujet_log
        self.mqtt_username = mqtt_username
        self.mqtt_certfile = mqtt_certfile
        self.mqtt_keyfile = mqtt_keyfile
        self.client = None

        if not self.utiliser_mqtt:
            return

        self.client = mqtt.Client(protocol=mqtt.MQTTv311)

        if self.port == 8883 and self.mqtt_certfile and self.mqtt_keyfile:
            self.client.tls_set(
                ca_certs=None,
                certfile=self.mqtt_certfile,
                keyfile=self.mqtt_keyfile,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
            )
            self.client.username_pw_set(username=self.mqtt_username, password=None)
            self.client.on_connect = self._on_connect

        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"[ERREUR FATALE] Impossible de se connecter au broker MQTT: {e}")
            self.utiliser_mqtt = False

    def publish(self, date, uid):
        if not self.utiliser_mqtt or not self.client:
            return
        uid_str = "-".join(str(octet) for octet in uid)
        info_carte = json.dumps({"date_heure": date, "uid": uid_str})

        try:
            self.client.publish(self.sujet_log, info_carte)
            print(f"[MQTT] Message publie a {self.sujet_log} : {info_carte}")
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur lors de la publication MQTT: {e}")

    def close(self):
        if not self.utiliser_mqtt or not self.client:
            return
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connexion reussie a {self.broker}")
        else:
            print(f"[MQTT] Echec de la connexion (RC={rc})")
