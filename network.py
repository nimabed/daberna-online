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
            return pickle.loads(self.client.recv(4096*2))
        except socket.error as e:
            print(f"Sending error: {e}")

    def send_for_object(self, data):
        try:
            self.client.send(data.encode())
            time.sleep(5)
            return self.client.recv(4096).decode()
        except socket.error as e:
            print(f"Send for object error: {e}")

