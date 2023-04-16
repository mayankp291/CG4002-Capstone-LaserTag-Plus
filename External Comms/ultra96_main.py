
from multiprocessing import Process, Queue, Lock, queues, Event
from AI import AI_Process
from MQTT import MQTT_Client
from RelayServer import Relay_Server
from EvaluationClient import Evaluation_Client
from GameEngine import Game_Engine
from constants import *


def main():
    eval_client = Evaluation_Client('localhost', 11001, 2, eval_queue, intcomms_queue, viz_queue,
                                    recv_queue, action_p1_queue, action_p2_queue, reloadSendRelayP1. reloadSendRelayP2)
    eval_client.start()

    ai_player_1 = AI_Process(imu_queue_p1, action_p1_queue)
    ai_player_1.start()

    ai_player_2 = AI_Process(imu_queue_p2, action_p2_queue)
    ai_player_2.start()

    game_engine = Game_Engine(action_p1_queue, action_p2_queue, viz_queue, eval_queue, recv_queue, processing, reloadSendRelayP1, reloadSendRelayP2,
                              grenadeP1Hit, grenadeP1Miss, grenadeP2Hit, grenadeP2Miss, shootP1Hit, shootP2Hit)
    game_engine.start()

    mqtt = MQTT_Client('cg4002/gamestate', 'cg4002/visualizer', 'ultra96',
                       2, viz_queue, grenadeP1Hit, grenadeP1Miss, grenadeP2Hit, grenadeP2Miss)
    mqtt.start()

    # HOST, PORT = "192.168.95.235", 11000
    HOST, PORT = "localhost", 11000
    server = Relay_Server(HOST, PORT, relayFlag, processing, shootP1Hit, shootP2Hit, imu_queue_p1, imu_queue_p2,
                          action_p1_queue, action_p2_queue, intcomms_queue, reloadSendRelayP1, reloadSendRelayP2)
    server.start()
    eval_client.join()
    ai_player_1.join()
    ai_player_2.join()
    game_engine.join()
    mqtt.join()
    server.join()


if __name__ == "__main__":
    main()
