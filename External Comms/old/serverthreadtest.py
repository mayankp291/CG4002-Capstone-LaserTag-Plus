import socket
import threading
import paho.mqtt.client as mqtt
import queue

class TCPClient:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address
        print(f'Accepted connection from {self.address}')
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        while self.running:
            data = self.socket.recv(1024)
            if not data:
                break
            TCPServer.mqtt_client.publish('test/cg4002', data)
        self.socket.close()

class TCPServer:
    client_sockets = []

    def __init__(self, address='0.0.0.0', port=11000):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, port))
        self.socket.listen(5)
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        while self.running:
            client_socket, client_address = self.socket.accept()
            client = TCPClient(client_socket, client_address)
            self.client_sockets.append(client)

    @staticmethod
    def on_message(client, userdata, message):
        print(f'Received MQTT message: {message.payload.decode()}')
        TCPServer.message_queue.put(message.payload)

    @staticmethod
    def handle_mqtt():
        while True:
            message = TCPServer.message_queue.get()
            for client in TCPServer.client_sockets:
                client.socket.send(message)

    @staticmethod
    def start():
        TCPServer.message_queue = queue.Queue()
        TCPServer.mqtt_client = mqtt.Client()
        TCPServer.mqtt_client.connect('test.mosquitto.org', 1883, 60)
        TCPServer.mqtt_client.subscribe('test/cg4002')
        TCPServer.mqtt_client.on_message = TCPServer.on_message
        TCPServer.mqtt_thread = threading.Thread(target=TCPServer.handle_mqtt)
        TCPServer.mqtt_thread.start()
        TCPServer.mqtt_client.loop_start()

if __name__ == '__main__':
    server = TCPServer()
    server.start()