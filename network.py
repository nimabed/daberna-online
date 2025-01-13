import socket, pickle, hashlib
from gctl import Game
# import game_pb2

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
        # checksum, serialized_game = raw_data.decode().split(":", 1)
        received_checksum = hashlib.sha256(serialized_game).hexdigest()
        if received_checksum != checksum:
            raise ValueError("Checksum mismatch!")
        else:
            return True


    def send(self, data):
        try:
            self.client.send(data.encode())

            if data == "ready":
                return pickle.loads(self.client.recv(1024))
            
            elif data == "get":
                checksum, serialized_game = self.client.recv(4096*5).decode().split(":", 1)
                serialized_bytes = serialized_game.encode()
                if self.check_seri(checksum, serialized_bytes):
                    game = Game()
                    game.deserialize(serialized_bytes)
                    return game
                else:
                    print("The checksums is not identical")
                # json_data = self.client.recv(4096).decode()
                # print(json_data)
                # deserialize = json.loads(json_data)
                # print(deserialize)
                # return msgpack.unpackb(self.client.recv(4096*3))
                # return pickle.loads(self.client.recv(30720))
                
                
            
        except socket.error as e:
            print(f"Sending error: {e}")
                   

# mynet = Network("192.168.1.9", 9999)

# mynet.send("get")