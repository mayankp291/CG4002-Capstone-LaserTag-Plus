import threading
 
class c1(threading.Thread) :
    def run(self) :
        for _ in range (2) :
            print(threading.currentThread().getName())
obj= c1(name='Hello')
obj1= c1(name='Bye')
obj.start()
obj1.start()

