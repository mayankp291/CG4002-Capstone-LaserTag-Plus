from socket import *
from Crypto import Random
from Crypto.Cipher import AES
import base64
import multiprocessing
from multiprocessing import Process, Queue

# with sshtunnel.open_tunnel(
#     ('stu.comp.nus.edu.sg', 443),
#     ssh_username="mayankp",
#     ssh_pkey="/var/ssh/rsa_key",
#     ssh_private_key_password="Sanchit@012345",
#     remote_bind_address=('192.168.95.219', 22),
#     local_bind_address=('0.0.0.0', 10022)
# ) as tunnel:
#     client = paramiko.SSHClient()
#     client.load_system_host_keys()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     client.connect('127.0.0.1', 10022)
#     # do some operations with client session
#     client.close()

# print('FINISH!')

# import sshtunnel
# from paramiko import SSHClient

# from sshtunnel import SSHTunnelForwarder

# server = SSHTunnelForwarder(
#     'stu.comp.nus.edu.sg',
#     ssh_username="mayankp",
#     ssh_password="Sanchit@012345",
#     remote_bind_address=('', 11000)
# )

# print("IT WORKSSS")

# server.start()


# print(server.local_bind_port)  # show assigned local port
# work with `SECRET SERVICE` through `server.local_bind_port`.

# from sshtunnel import SSHTunnelForwarder

#     # sshtunneling into sunfire
#     def start_tunnel(self):
#         # open tunnel to sunfire
#         tunnel1 = sshtunnel.open_tunnel(
#             # host for sunfire at port 22
#             ('stu.comp.nus.edu.sg', 22),
#             # ultra96 address
#             remote_bind_address = ('192.168.95.244', 22),
#             ssh_username = self.user,
#             ssh_password = self.passw,
#             block_on_close = False
#             )
#         tunnel1.start()
        
#         print('[Tunnel Opened] Tunnel into Sunfire: ' + str(tunnel1.local_bind_port))

#         # sshtunneling into ultra96
#         tunnel2 = sshtunnel.open_tunnel(
#             # ssh to ultra96
#             ssh_address_or_host = ('localhost', tunnel1.local_bind_port),
#             # local host
#             remote_bind_address=('127.0.0.1', self.port),
#             ssh_username = 'xilinx',
#             ssh_password = 'xilinx',
#             local_bind_address = ('127.0.0.1', self.port), #localhost to bind it to
#             block_on_close = False
#             )
#         tunnel2.start()
#         print('[Tunnel Opened] Tunnel into Xilinx')

#     #     return tunnel2.local_bind_address


# import paramiko
# import sshtunnel

# with sshtunnel.open_tunnel(
#     ('stu.comp.nus.edu.sg', 22),
#     ssh_username="mayankp",
#     ssh_pkey="/var/ssh/rsa_key",
#     ssh_private_key_password="Sanchit@012345",
#     remote_bind_address=('192.168.95.219', 22),
#     local_bind_address=('0.0.0.0', 10022)
# ) as tunnel:
#     client = paramiko.SSHClient()
#     client.load_system_host_keys()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     client.connect('127.0.0.1', 10022)
#     # do some operations with client session
#     client.close()

# print('FINISH!')

# serverName = gethostbyname('192.168.95.219')


# serverName = gethostbyname('localhost')
# serverPort = 11000


from socket import *
import json
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

KEY = b'PLSPLSPLSPLSWORK'
IV = b'PLSPLSPLSPLSWORK'

def our_cipher():
    return AES.new(KEY, AES.MODE_CBC, IV)


f = open('test.json')

def encrypt_AES(string):    
    msg = pad(string.encode("utf-8"), AES.block_size)
    ciphertext = our_cipher().encrypt(msg)
    ciphertext = base64.b64encode(IV + ciphertext)
    return ciphertext
    # return str(len(msg)).encode("utf-8") + "_".encode("utf-8") + ciphertext.encode("utf-8")

def decrypt_AES(ciphertext):
    ciphertext = base64.b64decode(ciphertext)
    dec_padding = our_cipher().decrypt(ciphertext[AES.block_size:])
    unpadded = unpad(dec_padding, AES.block_size)
    print(unpadded.decode())

k = Random.new().read(AES.block_size)
j = json.load(f)
# enc = encrypt_AES(json.dumps(j))
# print(enc)
# decrypt_AES(enc)






serverName = gethostbyname('localhost')
serverPort = 11000

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

# message = input('Enter message')

while(True):
    message = encrypt_AES(json.dumps(j))
    encodethis = json.dumps(j).encode("utf-8")
    add = str(len(message)) + "_"
    print("sending: ", message)
    clientSocket.send(add.encode("utf-8"))
    clientSocket.send(message) 
    recvMessage = clientSocket.recv(2048)
    print('from server: ', recvMessage.decode())

# server.stop()


