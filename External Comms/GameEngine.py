from PlayerState import Player
import time
from multiprocessing import Process, Queue, Event
from multiprocessing import queues
import json
from constants import *


class Game_Engine(Process):
    """
    The game engine is responsible for processing the actions of both players.
    It will also send the game state to the visualizer and the evaluation server.
    """
    def __init__(self, action_p1_queue, action_p2_queue, viz_queue, eval_queue, recv_queue, processing, reloadSendRelayP1, reloadSendRelayP2,
                 grenadeP1Hit, grenadeP1Miss, grenadeP2Hit, grenadeP2Miss, shootP1Hit, shootP2Hit):
        super().__init__()
        self.p1 = Player()
        self.p2 = Player()
        self.action_p1_queue = action_p1_queue
        self.action_p2_queue = action_p2_queue
        self.processing = processing
        self.reloadSendRelayP1 = reloadSendRelayP1
        self.reloadSendRelayP2 = reloadSendRelayP2
        self.viz_queue = viz_queue
        self.eval_queue = eval_queue
        self.recv_queue = recv_queue
        self.grenadeP1Hit = grenadeP1Hit
        self.grenadeP1Miss = grenadeP1Miss
        self.grenadeP2Hit = grenadeP2Hit
        self.grenadeP2Miss = grenadeP2Miss
        self.shootP1Hit = shootP1Hit
        self.shootP2Hit = shootP2Hit

    def run(self):
        """
        The game engine will run in a loop, waiting for both players actions.
        Once it gets both actions, it will process them and add the updated state to the respective queues to be sent to evaluation server and visualiser.
        It waits for recv_queue to get the updated state from the evaluation server.
        The loop will continue until both players logout.
        """
        # flow = get both player actions -> process actions -> send to visualizer and eval server -> get updated state from eval server
        while True:
            action_p1, action_p2 = 'none', 'none'
            self.p1.update_shield_time()
            self.p2.update_shield_time()

            # get both player actions
            try:
                print("[DEBUG] Ready to get player actions")
                action_p1 = self.action_p1_queue.get(timeout=30)
                action_p2 = self.action_p2_queue.get(timeout=30)
            except Exception as e:
                print("Game Engine: Timeout waiting for player actions")
                try:
                    while True:
                        self.action_p1_queue.get_nowait()
                except queues.Empty:
                    pass
                try:
                    while True:
                        self.action_p2_queue.get_nowait()
                except queues.Empty:
                    pass
                print("Game Engine: Resetting player actions")
                self.processing.clear()
                continue
                
            print("[DEBUG]", self.processing.is_set(), action_p1, action_p2)

            # set flag for processing, blocks other processes
            self.processing.set()

            action_p1_viz = action_p1
            action_p2_viz = action_p2

            # logout
            if action_p1 == "logout" and action_p2 == "logout":
                self.p1.logout()
                self.p2.logout()
            elif action_p1 == "logout":
                self.p1.logout()
                action_p1_viz = "none"
            elif action_p2 == "logout":
                self.p1.logout()
                action_p2_viz = "none"

            # shield
            if action_p1 == "shield":
                self.p1.shield()

            if action_p2 == "shield":
                self.p2.shield()

            # reload
            if action_p1 == "reload":
                if self.p1.bullets <= 0:
                    self.reloadSendRelayP1.set()
                self.p1.reload()

            if action_p2 == "reload":
                if self.p2.bullets <= 0:
                    self.reloadSendRelayP2.set()
                self.p2.reload()

            if action_p1 == "shoot" or action_p2 == "shoot":
                action_p1_viz, action_p2_viz = self.triggerShoot(
                    action_p1, action_p2)

            if action_p1 == "grenade" or action_p2 == "grenade":
                action_p1_viz, action_p2_viz = self.triggerGrenade(
                    action_p1_viz, action_p2_viz)

            self.p1.update_shield_time()
            self.p2.update_shield_time()
            viz_dict = {"p1": self.p1.get_dict(), "p2": self.p2.get_dict()}
            viz_dict["p1"]["action"] = action_p1_viz
            viz_dict["p2"]["action"] = action_p2_viz
            self.viz_queue.put(('STATE', json.dumps(viz_dict)))
            eval_dict = {"p1": self.p1.get_dict(), "p2": self.p2.get_dict()}
            # print("[INTERNAL STATE]", eval_dict)
            self.eval_queue.put(json.dumps(eval_dict))

            # clear all the flags
            self.shootP1Hit.clear()
            self.shootP2Hit.clear()
            self.grenadeP1Hit.clear()
            self.grenadeP2Hit.clear()
            self.grenadeP1Miss.clear()
            self.grenadeP2Miss.clear()
            # sync states
            try:
                recv_state = self.recv_queue.get(timeout=5)
                self.p1.initialize_from_dict(recv_state["p1"])
                self.p2.initialize_from_dict(recv_state["p2"])
            except:
                print("RECV queue is empty")

            # clear processing flag
            self.processing.clear()

    def triggerShoot(self, action_p1, action_p2):
        """
        Trigger shoot action and update internal state
        """
        action_p1_viz = action_p1
        action_p2_viz = action_p2
        isPlayerOneShootInvalid = (self.p1.bullets <= 0)
        isPlayerTwoShootInvalid = (self.p2.bullets <= 0)
        # both shoot
        if action_p1 == "shoot" and action_p2 == "shoot":
            self.p1.shoot()
            self.p2.shoot()
            start_time = time.time()
            # check until time, if vest not recv send as miss
            while time.time() - start_time < SHOOT_MAX_TIME_LIMIT:
                # as both are in range of each other only one needs to be checked
                if self.shootP1Hit.is_set() or self.shootP2Hit.is_set():
                    # udpate internal state for shoot hit
                    self.p1.shoot_hit()
                    self.p2.shoot_hit()
                    action_p1_viz = "shoot_p2_hits"
                    action_p2_viz = "shoot_p1_hits"
                    break
            if not self.shootP1Hit.is_set() and not self.shootP2Hit.is_set():
                # clear flags
                action_p1_viz = "shoot_p2_misses"
                action_p2_viz = "shoot_p1_misses"
            if isPlayerOneShootInvalid:
                action_p1_viz = "shoot_p2_invalid"
            if isPlayerTwoShootInvalid:
                action_p2_viz = "shoot_p1_invalid"
        elif action_p1 == "shoot":
            self.p1.shoot()
            start_time = time.time()
            while time.time() - start_time < SHOOT_MAX_TIME_LIMIT:
                if self.shootP2Hit.is_set():
                    self.p2.shoot_hit()
                    action_p1_viz = "shoot_p2_hits"
                    break
            if not self.shootP2Hit.is_set():
                if isPlayerOneShootInvalid:
                    action_p1_viz = "shoot_p2_invalid"
                else:
                    action_p1_viz = "shoot_p2_misses"
        else:
            self.p2.shoot()
            start_time = time.time()
            while time.time() - start_time < SHOOT_MAX_TIME_LIMIT:
                if self.shootP1Hit.is_set():
                    self.p1.shoot_hit()
                    action_p2_viz = "shoot_p1_hits"
                    break
            if not self.shootP1Hit.is_set():
                if isPlayerTwoShootInvalid:
                    action_p2_viz = "shoot_p1_invalid"
                else:
                    action_p2_viz = "shoot_p1_misses"
        return action_p1_viz, action_p2_viz

    def triggerGrenade(self, action_p1, action_p2):
        """
        Trigger grenade action and update internal state
        """
        action_p1_viz = "none"
        action_p2_viz = "none"
        isPlayerOneGrenadeInvalid = (self.p1.grenades <= 0)
        isPlayerTwoGrenadeInvalid = (self.p2.grenades <= 0)
        if action_p1 == "grenade" and action_p2 == "grenade":
            self.p1.grenade()
            self.p2.grenade()
            if isPlayerOneGrenadeInvalid and isPlayerTwoGrenadeInvalid:
                # when two players have insufficient number of grenades
                return action_p1, action_p2
            start_time = time.time()
            send_dict = {"p1": self.p1.get_dict(), "p2": self.p2.get_dict()}
            send_dict["p1"]["action"] = action_p1
            send_dict["p2"]["action"] = action_p2
            # send check
            self.viz_queue.put(('CHECK', json.dumps(send_dict)))
            # wait for 3 sec
            while (time.time() - start_time) < GRENADE_MAX_TIME_LIMIT:
                # as both are in range of each other only one needs to be checked
                if self.grenadeP1Hit.is_set() or self.grenadeP2Hit.is_set():
                    if not isPlayerOneGrenadeInvalid:
                        self.p1.grenade_hit()
                        action_p1_viz = "grenade_p2_hits"
                    if not isPlayerTwoGrenadeInvalid:
                        self.p2.grenade_hit()
                        action_p2_viz = "grenade_p1_hits"
                    break
                elif self.grenadeP1Miss.is_set() or self.grenadeP2Miss.is_set():
                    if not isPlayerOneGrenadeInvalid:
                        action_p1_viz = "grenade_p2_misses"
                    if not isPlayerTwoGrenadeInvalid:
                        action_p2_viz = "grenade_p1_misses"
                    break
        elif action_p1 == "grenade":
            self.p1.grenade()
            if isPlayerOneGrenadeInvalid:
                # when player one have insufficient number of grenades
                return action_p1, action_p2
            send_dict = {"p1": self.p1.get_dict(), "p2": self.p2.get_dict()}
            send_dict["p1"]["action"] = action_p1
            send_dict["p2"]["action"] = action_p2
            self.viz_queue.put(('CHECK', json.dumps(send_dict)))
            start_time = time.time()
            while time.time() - start_time < GRENADE_MAX_TIME_LIMIT:
                if self.grenadeP2Hit.is_set():
                    self.p2.grenade_hit()
                    action_p1_viz = "grenade_p2_hits"
                    break
                elif self.grenadeP2Miss.is_set():
                    action_p1_viz = "grenade_p2_misses"
                    break
        else:
            self.p2.grenade()
            if isPlayerTwoGrenadeInvalid:
                # when player two have insufficient number of grenades
                return action_p1, action_p2
            send_dict = {"p1": self.p1.get_dict(), "p2": self.p2.get_dict()}
            send_dict["p1"]["action"] = action_p1
            send_dict["p2"]["action"] = action_p2
            self.viz_queue.put(('CHECK', json.dumps(send_dict)))
            start_time = time.time()
            while time.time() - start_time < GRENADE_MAX_TIME_LIMIT:
                if self.grenadeP1Hit.is_set():
                    self.p1.grenade_hit()
                    action_p2_viz = "grenade_p1_hits"
                    break
                elif self.grenadeP1Miss.is_set():
                    action_p2_viz = "grenade_p1_misses"
                    break
        return action_p1_viz, action_p2_viz

