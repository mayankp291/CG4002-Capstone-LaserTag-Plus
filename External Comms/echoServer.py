from socket import *

serverPort = 2105
serverName = gethostbyname('localhost')

# initial connection setup
serverSocket = socket(AF_INET, SOCK_STREAM)
# bind to listen at the port
serverSocket.bind(('', serverPort))
serverSocket.listen()
print('Server is ready to receive')


connectionSocket, clientAddr = serverSocket.accept() 
for _ in range(100):
    recvMessage = connectionSocket.recv(2048)
    print('from server: ', recvMessage.decode())

    connectionSocket.send(recvMessage)
connectionSocket.close()