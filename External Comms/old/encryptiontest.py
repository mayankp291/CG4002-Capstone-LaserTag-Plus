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
    # iv = Random.new().read(AES.block_size)
    # cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = base64.b64encode(IV + our_cipher().encrypt(msg))
    msg = ciphertext.encode("utf-8")
    return ciphertext

def decrypt_AES(ciphertext):
    ciphertext = base64.b64decode(ciphertext)
    dec_padding = our_cipher().decrypt(ciphertext[AES.block_size:])
    unpadded = unpad(dec_padding, AES.block_size)
    print(unpadded.decode())

k = Random.new().read(AES.block_size)
j = json.load(f)
enc = encrypt_AES(json.dumps(j))
print(enc)
decrypt_AES(enc)



