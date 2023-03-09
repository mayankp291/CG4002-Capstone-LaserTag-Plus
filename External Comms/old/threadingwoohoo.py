import json
import socket
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad,unpad

HOST = 'localhost'  # The server's hostname or IP address
PORT = 11001 

# Secret key and initialization vector
key = b'PLSPLSPLSPLSWORK'
# iv = b'Sixteen byte iv__'
# iv = Random.new().read(AES.block_size)
iv = b'PLSPLSPLSPLSWORK'


# AES cipher object
cipher = AES.new(key, AES.MODE_CBC, iv)

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    f = open('test.json')
    plaintext = json.load(f)
    json_string = json.dumps(plaintext)
    coded_string = json_string.encode()
    length_json = len(coded_string)
    encrypted_text = encrypt(json_string.encode())
    m = (str(len(encrypted_text))+"_").encode('utf-8')
    # text_to_be_sent = str(length_json)+""+"_"+str(encrypted_text)
    f.close()
    # c=0
    val = 0
    val = input("Please enter any number to send a random game state to the eval_server = ")
    while True and val!=0:  
        client.send(m)
        client.send(encrypted_text)
        #############################
        data = ""
        data = client.recv(2048).decode("utf-8")
        print("=====================================")
        print("[GROUND TRUTH RECEIVED FROM SERVER]") 
        print({data})
        print("=====================================")
        val = 0
        val = input("Please enter any number to send a random game state to the eval_server = ")
        
        ##############################
        # data = b''
        # c=1
        # while len(data) != 0 or c==1:
        #     _d = client.recv(len(data))
        #     if not _d:
        #         data = b''
        #         c=2
        #         break
        #     data += _d
        #     # data = data.decode('utf-8')
        #     print("[GROUND TRUTH RECEIVED FROM SERVER]") 
        #     print({data})
        #     val = 0
        #     val = input("Please enter any number to send a random game state to the eval_server = "

    # Encryption
def encrypt(plaintext):
    padded_plaintext = pad(plaintext, AES.block_size)
    ciphertext = base64.b64encode(iv+cipher.encrypt(padded_plaintext))
    return ciphertext

# def decrypt_message(cipher_text):
#         """
#         This function decrypts the response message received from the Ultra96 using the secret encryption key
#         that was entered in this script during initial connection by the Ultra96.
#         It returns a dictionary containing the action detected by the Ultra96.
#         """
#         decoded_message = base64.b64decode(cipher_text)                            # Decode message from base64 to bytes
#         iv              = decoded_message[:AES.block_size]                                     # Get IV value
#         # secret_key      = bytes(str(secret_key), encoding="utf8")  
#         #           # Convert secret key to bytes
#         secret_key = bytes("PLSPLSPLSPLSWORK".encode("utf-8"))
#         cipher = AES.new(secret_key, AES.MODE_CBC, iv)                              # Create new AES cipher object

#         decrypted_message = cipher.decrypt(decoded_message[AES.block_size:])  # Perform decryption
#         decrypted_message = unpad(decrypted_message, AES.block_size)
#         decrypted_message = decrypted_message.decode('utf8')  # Decode bytes into utf-8

#         ret = json.loads(decrypted_message)
#         return ret

main()