import sshtunnel
from socket import *
from paramiko import SSHClient

SUNFIRE_USERNAME ="mayankp"
SUNFIRE_PASSWORD = "Sanchit@012345"
XILINX_USERNAME = "xilinx"
XILINX_PASSWORD = "plsdonthackus"
SIZE = 1024
FORMAT = "utf-8"
dataa="HELLO WORLD"

SUNFIRE = "stu.comp.nus.edu.sg"
XILINX = "192.168.95.219"
LOCAL_HOST = 'localhost'
# LOCAL_HOST = "127.0.0.1"
SSH_PORT = 22
PORT = 11000 #listening port of Ultra96 and relay laptop

tunnel1 = sshtunnel.open_tunnel(
    ssh_address_or_host = (SUNFIRE, SSH_PORT),
    remote_bind_address = (XILINX, SSH_PORT),
    ssh_username = SUNFIRE_USERNAME,
    ssh_password = SUNFIRE_PASSWORD,
    block_on_close = False
)
tunnel1.start() 
#laptop to stu
print(f'Connection to tunnel1 {SUNFIRE}:{SSH_PORT} established')
print("LOCAL PORT:", tunnel1.local_bind_port)

tunnel2 = sshtunnel.open_tunnel(
    ssh_address_or_host = (LOCAL_HOST, tunnel1.local_bind_port),
    remote_bind_address = (LOCAL_HOST, PORT),
    ssh_username = XILINX_USERNAME,
    ssh_password = XILINX_PASSWORD,
    local_bind_address = (LOCAL_HOST, PORT),
    block_on_close = False
)
tunnel2.start()
print(f'Connection to tunnel2 {XILINX}:{PORT} established')
print("LOCAL PORT:", tunnel2.local_bind_port)

ADDR = (XILINX, tunnel2.local_bind_port)
print(ADDR)




serverName = gethostbyname('localhost')
# serverName = gethostbyname('192.168.95.219')
# serverPort = tunnel1.local_bind_port
serverPort = 11000

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

# message = input('Enter message')
message = "Hello der"
for _ in range(100):
    clientSocket.send(message.encode())
    recvMessage = clientSocket.recv(2048)
    print('from server: ', recvMessage.decode())
clientSocket.close()

tunnel2.close()
tunnel1.close()