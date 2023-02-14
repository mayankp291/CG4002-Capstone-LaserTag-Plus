# Ultra96 Server
from multiprocessing import Process, Queue
import json
import paho.mqtt.client as mqtt
import threading
import random

imu_queue = Queue()
action_queue = Queue()
viz_queue = Queue()


player_state = {
    "p1":
    {
        "hp": 100,
        "action": "none",
        "bullets": 6,
        "grenades": 2,
        "shield_time": 0,
        "shield_health": 0,
        "num_deaths": 0,
        "num_shield": 3
    },
    "p2":
    {
        "hp": 100,
        "action": "none",
        "bullets": 6,
        "grenades": 2,
        "shield_time": 0,
        "shield_health": 0,
        "num_deaths": 0,
        "num_shield": 3
    }
}



class Game_Engine(threading.Thread):
    def __init__(self):
        super().__init__()
    
    def run(self):
        while True:
            if not imu_queue.empty():
                imu_data = imu_queue.get()
                self.AI_random(imu_data)

            if not action_queue.empty():
                action = action_queue.get()
                print("[ACTION]", action)
                # Update action for player 1
                if action != 'grenade_p2_hits':
                    player_state['p1']['action'] = action
                # Update player 1 state (active player) and player 2 state (passive player)
                if action == 'reload':
                    player_state['p1']['bullets'] = 6
                elif action == 'grenade':
                    # update grenade for player 1
                    player_state['p1']['grenades'] -= 1
                    # send check for player 2
                    viz_queue.put('check_grenade')
                elif action == 'grenade_p2_hits':
                    player_state['p2']['hp'] -= 30
                elif action == 'shield':
                    player_state['p1']['num_shield'] -= 1
                    player_state['p1']['shield_time'] = 10
                    player_state['p1']['shield_health'] = 30
                elif action == 'shoot':
                    player_state['p1']['bullets'] -= 1
                    # TODO check if player 2 is in shield
                    player_state['p2']['hp'] -= 10
                
                # rebirth for player 2
                if player_state['p2']['hp'] <= 0:
                    # reset player 2 stats
                    player_state['p2']['hp'] = 0
                    player_state['p2']['num_deaths'] += 1
                    player_state['p2']['bullets'] = 6
                    player_state['p2']['grenades'] = 2
                    player_state['p2']['num_shield'] = 3
                    player_state['p2']['shield_time'] = 0
                    player_state['p2']['shield_health'] = 0
                
                # print("[PLAYER STATE FROM GAME ENGINE]", player_state)
                viz_queue.put(player_state) 


    def AI_random(self, imu_data):
        print(imu_data)
        AI_actions = ['reload', 'grenade', 'shield', 'shoot']
        action = random.choice(AI_actions)
        action_queue.put(action)

    def eval_check(self, player_State):
        pass


# MQTT Client to send data to AWS IOT Core
class MQTT_Client(threading.Thread):
    def __init__(self, pub_topic, sub_topic, client_id, group) -> None:
        super().__init__()
        self.pub_topic = pub_topic
        self.sub_topic = sub_topic
        self.client_id = client_id
        self.group = group
        self.client = mqtt.Client(client_id)
        self.client.connect("test.mosquitto.org", 1883, 60)
        print('MQTT Client started on', self.client_id)
        self.client.subscribe(self.sub_topic)
        self.client.on_message = self.receive
    
    def run(self):
        while True:
            data = viz_queue.get()
            # print("[PUBLISH]", data)
            self.publish(str(data))

    def publish(self, message):
        self.client.publish(self.pub_topic, message)
        print('Published message to', self.pub_topic, message)
    
    def receive(self, client, userdata, message):
        print("Received message from", message.topic, message.payload)
        if message.payload == b'grenade':
            # to update grenade damage for player 2
            action_queue.put('grenade_p2_hits') 


def main():
    game_engine = Game_Engine()
    game_engine.daemon = True
    game_engine.start()

    mqtt = MQTT_Client('cg4002/gamestate', 'cg4002/visualiser', 'testpc', 2)
    mqtt.daemon = True
    mqtt.start()

    mqtt.client.loop_forever()

if __name__ == "__main__":
    main()