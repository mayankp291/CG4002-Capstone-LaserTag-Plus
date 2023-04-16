import queue

class MyClass:
    def __init__(self, my_queue):
        self.my_queue = my_queue

    def add_item(self, item):
        self.my_queue.put(item)

# Create a queue object
my_queue = queue.Queue()

# Pass the queue to an instance of MyClass
my_class = MyClass(my_queue)

# Add an item to the queue through MyClass
my_class.add_item("hello")

# Check the contents of the queue outside of MyClass
print(my_queue.get())  # Output: "hello"
