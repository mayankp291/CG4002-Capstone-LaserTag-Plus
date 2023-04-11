import paho.mqtt.client as mqtt
import json
from multiprocessing import Process, Event
from constants import MQTT_USERNAME, MQTT_PASSWORD


class MQTT_Client(Process):
    """
    A process that handles MQTT communication.
    """
    def __init__(self, pub_topic, sub_topic, client_id, group, viz_queue, grenadeP1Hit, grenadeP1Miss, grenadeP2Hit, grenadeP2Miss) -> None:
        """
        Initializes the MQTT_Client process.
        
        Args:
        pub_topic (str): The topic to publish to.
        sub_topic (str): The topic to subscribe to.
        client_id (str): The client ID to use.
        group (str): The group ID to use.
        viz_queue (Queue): The queue used to send data to the visualization process.
        grenadeP1Hit (Event): An event flag indicating that player 1 has been hit by a grenade.
        grenadeP1Miss (Event): An event flag indicating that player 1 has missed a grenade.
        grenadeP2Hit (Event): An event flag indicating that player 2 has been hit by a grenade.
        grenadeP2Miss (Event): An event flag indicating that player 2 has missed a grenade.
        """
        super().__init__()
        self.pub_topic = pub_topic
        self.sub_topic = sub_topic
        self.client_id = client_id
        self.group = group
        self.client = mqtt.Client(client_id, protocol=mqtt.MQTTv311)
        # self.client = mqtt.Client(client_id)
        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLSv1_2)
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.connect(
            "e56e6e3e03d54e70bf9cc69a2761fe4c.s1.eu.hivemq.cloud", 8883)
        print('MQTT Client started on', self.client_id)
        self.client.subscribe(self.sub_topic)
        self.client.on_message = self.receive
        self.viz_queue = viz_queue
        self.grenadeP1Hit = grenadeP1Hit
        self.grenadeP1Miss = grenadeP1Miss
        self.grenadeP2Hit = grenadeP2Hit
        self.grenadeP2Miss = grenadeP2Miss

    def run(self):
        try:
            self.client.loop_start()
            while True:
                type, data = self.viz_queue.get()
                # print("[PUBLISH]", data)
                self.publish(type, json.loads(data))
        except Exception as e:
            print(e)
            self.client.loop_stop()

    def publish(self, type, data):
        """	
        Publishes a message to the MQTT broker.

        Args:
        type (str): The type of message to publish.
        data (str): The data to publish.
        """
        try:
            data = str(data)
            message = str(len(data)) + '_' + type + '_' + data
            self.client.publish(self.pub_topic, message)
            print('====================================')
            print('[MQTT] Published message to visualiser at',
                  self.pub_topic, message)
            print('====================================')
        except:
            print("Error: could not publish message")

    def receive(self, client, userdata, message):
        """
        Receives a message from the MQTT broker.	
        
        Args:
        client (Client): The client instance for this callback.
        userdata (object): The private user data as set in Client() or userdata_set().
        message (MQTTMessage): An instance of MQTTMessage. This is a class with members topic, payload, qos, retain.
        """
        try:
            print("[MQTT] " + message.payload.decode("utf-8"))
            msg = message.payload.decode("utf-8")

            if msg == "14_CHECK_grenade_p2_hit":
                # to update grenade damage for player 2
                print("[MQTT] Player 2 is in grenade range")
                self.grenadeP2Hit.set()
            elif msg == '15_CHECK_grenade_p2_miss':
                print("[MQTT] Player 2 is not in grenade range")
                self.grenadeP2Miss.set()

            elif msg == '14_CHECK_grenade_p1_hit':
                print("[MQTT] Player 1 is in grenade range")
                self.grenadeP1Hit.set()
            elif msg == '15_CHECK_grenade_p1_miss':
                print("[MQTT] Player 1 is not in grenade range")
                self.grenadeP1Miss.set()
            elif msg == '6_CHECK_update':
                pass
        except Exception as e:
            print('Error: message not in correct format')
            print(message.payload)
            print(e)
