from socket import *
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from multiprocessing import Process, Queue, Lock, queues, Event
from constants import *
import json



class Evaluation_Client(Process):
    """	
    A process that sends updated states to the Evaluation Server and gets back expected states.
    The expected states are sent to visualizer, game engine and relay laptop.
    """

    IV = b'PLSPLSPLSPLSWORK'
    KEY = b'PLSPLSPLSPLSWORK'

    def __init__(self, ip, port, group, eval_queue, intcomms_queue, viz_queue, recv_queue, action_p1_queue, action_p2_queue, reloadSendRelayP1, reloadSendRelayP2) -> None:
        """
        Initializes the Evaluation Client process.

        Args:
        ip (str): The IP address of the Evaluation Server.
        port (int): The port number of the Evaluation Server.
        group (int): The one player or two player game.
        eval_queue (Queue): The queue used to send updated states to Evaluation Server.
        intcomms_queue (Queue): The queue to send expected states to Internal Comms.
        viz_queue (Queue): The queue used to send updated states to Visualiser.
        recv_queue (Queue): The queue used to updated internal states from Evaluation Server.
        action_p1_queue (Queue): The queue that contains actions of player 1.
        action_p2_queue (Queue): The queue that contains actions of player 2.
        reloadSendRelayP1 (Event): An event flag indicating player 1 has reloaded.
        reloadSendRelayP2 (Event): An event flag indicating player 2 has reloaded.
        """
        super().__init__()
        self.eval_ip = gethostbyname(ip)
        self.eval_port = port
        self.group = group
        self.eval_queue = eval_queue
        self.intcomms_queue = intcomms_queue
        self.viz_queue = viz_queue
        self.recv_queue = recv_queue
        self.action_p1_queue = action_p1_queue
        self.action_p2_queue = action_p2_queue
        self.reloadSendRelayP1 = reloadSendRelayP1
        self.reloadSendRelayP2 = reloadSendRelayP2

        try:
            self.clientSocket = socket(AF_INET, SOCK_STREAM)
            self.clientSocket.connect((self.eval_ip, self.eval_port))
            evalServerConnected.set()
            print('Connected to Evaluation Server',
                  self.eval_ip, self.eval_port)
        except:
            print('Failed to connect to Evaluation Server',
                  self.eval_ip, self.eval_port)
            self.clientSocket = None

    def run(self):
        """
        The main function of the Evaluation Client process.
        Sends updated states to Evaluation Server and receives expected states.
        """
        try:
            while True:
                data = self.eval_queue.get()
                self.player_state = json.loads(data)
                self.send(data)
                self.receive()
        except Exception as e:
            print('Failed to send message to Evaluation Server',
                  self.eval_ip, self.eval_port)
            print(e)
            self.close()

    # Initialise AES Cipher

    @staticmethod
    def AES_Cipher():
        """
        Initializes the AES Cipher.
        """	
        return AES.new(Evaluation_Client.KEY, AES.MODE_CBC, Evaluation_Client.IV)

    def send(self, message):
        """
        Sends a message to the Evaluation Server.
        """
        if self.clientSocket is not None:
            try:
                encryted_message = self.encrypt_AES(message)
                len_info = str(len(encryted_message)) + "_"
                # send len_
                self.clientSocket.send(len_info.encode("utf-8"))
                self.clientSocket.send(encryted_message)
                print('=====================================')
                print('[EVAL CLIENT] Sent message to Evaluation Server',
                      self.eval_ip, self.eval_port, message)
                print('=====================================')
            except Exception as e:
                print('[EVAL CLIENT] Failed to send message to Evaluation Server',
                      self.eval_ip, self.eval_port, message)
                print(e)
                self.close()

    def receive(self):
        """
        Receives a message from the Evaluation Server.
        Once the state is received the internal action queues are cleared to not have old actions.
        The updated state is sent to the visualizer, internal comms and the relay laptop by putting them in their respective queues.
        """
        if self.clientSocket is not None:
            # global player_state
            try:
                # recv length followed by '_' followed by cypher
                data = b''
                while not data.endswith(b'_'):
                    _d = self.clientSocket.recv(1)
                    if not _d:
                        data = b''
                        break
                    data += _d
                if len(data) == 0:
                    print('no more data from the client')
                    self.stop()

                data = data.decode("utf-8")
                length = int(data[:-1])

                data = b''
                while len(data) < length:
                    _d = self.clientSocket.recv(length - len(data))
                    if not _d:
                        data = b''
                        break
                    data += _d
                if len(data) == 0:
                    print('no more data from the client')
                    self.stop()
                recv_dict = data.decode("utf8")  # D1ode raw bytes to UTF-8
                # recv_dict = literal_eval(msg)
                recv_dict = json.loads(recv_dict)
                player_state_intcomms['p1']['action'] = recv_dict['p1']['action']
                player_state_intcomms['p2']['action'] = recv_dict['p2']['action']
                player_state_intcomms['p1']['hp'] = recv_dict['p1']['hp']
                player_state_intcomms['p2']['hp'] = recv_dict['p2']['hp']
                player_state_intcomms['p1']['bullets'] = recv_dict['p1']['bullets']
                player_state_intcomms['p2']['bullets'] = recv_dict['p2']['bullets']
                # player_state = recv_dict
                action_p1 = recv_dict['p1']['action']
                action_p2 = recv_dict['p2']['action']
                if action_p1 != "logout" and action_p2 != "logout":
                    recv_dict['p1']['action'] = 'none'
                    recv_dict['p2']['action'] = 'none'
                if action_p1 == "shield" and self.player_state['p1']['action'] != "shield":
                    recv_dict['p1']['action'] = 'shield'
                if action_p2 == "shield" and self.player_state['p2']['action'] != "shield":
                    recv_dict['p2']['action'] = 'shield'
                self.viz_queue.put(('STATE', json.dumps(recv_dict)))

                self.intcomms_queue.put(json.dumps(player_state_intcomms))

                print('=====================================')
                print(
                    "[EVAL SERVER] Received message from Evaluation Server", recv_dict)
                print('=====================================')


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
                # sync internal state
                recv_dict['p1']['action'] = action_p1
                recv_dict['p2']['action'] = action_p2
                if action_p1 == "reload":
                    self.reloadSendRelayP1.set()
                if action_p2 == "reload":
                    self.reloadSendRelayP2.set()
                self.recv_queue.put(recv_dict)

            except:
                print('Failed to receive message from Evaluation Server',
                      self.eval_ip, self.eval_port)
                self.close()

    def close(self):
        """
        Closes the connection to the Evaluation Server.
        """
        if self.clientSocket is not None:
            self.clientSocket.close()
            print('Closed connection to Evaluation Server',
                  self.eval_ip, self.eval_port)

    def encrypt_AES(self, string):
        """
        Encrypts a string using AES.
        """
        msg = pad(string.encode("utf-8"), AES.block_size)
        encrypted_text = Evaluation_Client.AES_Cipher().encrypt(msg)
        ciphertext = base64.b64encode(self.IV + encrypted_text)
        return ciphertext

