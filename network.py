import socket, pickle

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
            if data.isdigit() or data == "start":
                return
            else:
                # return msgpack.unpackb(self.client.recv(4096*3))
                return pickle.loads(self.client.recv(30720))
                
                
            
        except socket.error as e:
            print(f"Sending error: {e}")
                   

# mynet = Network("192.168.1.9", 9999)

# mynet.send("ready")