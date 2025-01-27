import socket, pickle, hashlib, struct
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

    def check_seri(self, check_game_byte):
        received_checksum = hashlib.sha256(check_game_byte[64:]).hexdigest()
        return received_checksum.encode() == check_game_byte[:64]

    def received_message(self, count_byte):
        data_bytes = bytearray()
        while len(data_bytes) < count_byte:
            packet = self.client.recv(count_byte - len(data_bytes))
            if not packet:
                return
            data_bytes.extend(packet)
        return bytes(data_bytes)
    
    def received_all(self):
        bytes_length = self.received_message(4)
        if not bytes_length:
            return
        message_length = struct.unpack("I", bytes_length)[0]

        message_bytes = self.received_message(message_length)
        if not message_bytes:
            return
        
        return message_bytes

    def send(self, data):
        try:
            self.client.send(data.encode())

            if data == "ready":
                return pickle.loads(self.client.recv(4096))
            
            elif data == "get":
                data_recv = self.received_all()
                if data_recv and self.check_seri(data_recv):
                    game = Game(2)
                    game.deserialize(data_recv[64:])
                    return game
                else:
                    print("Checksum mismatch!")
                    print(data_recv)
                    return
                   
        except socket.error as e:
            print(f"Sending error: {e}")

    def receive_cards(self):
        return pickle.loads(self.client.recv(4096))
                   