### TESTING ENCODING
from ast import literal_eval

data = {'playerID': 2, 'beetleID': 4, 'sensorData': {'aX': 409, 'aY': 158, 'aZ': 435, 'gX': 265, 'gY': 261, 'gZ': 261}}

### send using len_encode(data)

def send(data):
    msg = str(data)
    msg = str(len(msg)) + '_' + msg
    return msg.encode("utf-8")

def recv(data):
    msg = data.decode("utf-8")
    # check len
    arr = msg.split("_")
    if arr[0] == len(arr[1]):
        print("Message Length Check: PASSED")
    msg = literal_eval(arr[1])
    print(msg)

a = send(data)
recv(a)



a = literal_eval(str(data))
print(a)