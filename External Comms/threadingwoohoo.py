from multiprocessing import Queue
import threading
import random
import time

e1 = threading.Event()
e2 = threading.Event()
e1.set()
e2.set()


def put_queue(q):
    while(e1.is_set()):
        time.sleep(1)
        a = random.randint(0, 100)
        q.put(a)
        print('put', a)
    

def get_queue(q):
    while(e2.is_set()):
        print('get',q.get())


q = Queue()
t = threading.Thread(target=put_queue, args=(q,))
t2 = threading.Thread(target=get_queue, args=(q,))
t.start()
t2.start()

time.sleep(10)
e1.clear()
e2.clear()
print('FINISH!')

### use events to break threads