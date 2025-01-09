import socket, pickle, time

class Network:
    def __init__(self, ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.player = self.connect()

    def get_p(self):
        return int(self.player)


    def connect(self):
        try:
            self.client.connect((self.ip, self.port))
            return self.client.recv(1024).decode()
        except socket.error as e:
            print(f"Connection error: {e}")

    def send(self, data):
        try:
            self.client.send(data.encode())
            return pickle.loads(self.client.recv(4096*3))
        except socket.error as e:
            print(f"Sending error: {e}")
            
    # Adding receive method
    def receive(self):
        return self.client.recv(1024).decode()        

