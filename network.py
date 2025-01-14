import socket, pickle, hashlib
from gctl import Game

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

    def check_seri(self, checksum, serialized_game):
        received_checksum = hashlib.sha256(serialized_game).hexdigest()
        return received_checksum == checksum

    def send(self, data):
        try:
            self.client.send(data.encode())

            if data == "ready":
                return pickle.loads(self.client.recv(1024))
            
            elif data == "get":
                check_list = self.client.recv(4096*5).decode().split(":")
                if len(check_list) == 2:
                    checksum, serialized_game = check_list
                    if self.check_seri(checksum, serialized_game.encode()):
                        game = Game()
                        game.deserialize(serialized_game.encode())
                        return game
                    else:
                        print("Checksum mismatch!")
                        return
                else:
                    print("The checksum list shorter than 2")
                    return
                   
        except socket.error as e:
            print(f"Sending error: {e}")
                   

# mynet = Network("192.168.1.9", 9999)

# mynet.send("get")