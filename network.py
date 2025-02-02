import socket, pickle, hashlib, struct
from gctl import Game

class Network:
    def __init__(self, ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.player = self.connect()
        self.game = Game(2)

    def get_p_id(self):
        return int(self.player[0])

    def get_num_of_p(self):
        return int(self.player[1])

    def connect(self):
        try:
            self.client.connect((self.ip, self.port))
            return self.client.recv(1024).decode().split(":")
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
                    # game = Game(2)
                    self.game.deserialize(data_recv[64:])
                    return self.game
                else:
                    print("Checksum mismatch!")
                    print(data_recv)
                    return
                   
        except socket.error as e:
            print(f"Sending error: {e}")

    def receive_cards(self):
        received_bytes = self.received_all()
        if received_bytes and self.check_seri(received_bytes):
            players_cards = self.game.deserialize_cards(received_bytes[64:])
            return players_cards
        else:
            print("Checksum mismatch!!!!")
            return
        # return pickle.loads(self.client.recv(4096*5))
        
                   

# mydict = {1: [[['*', '*', '4'], ['19', '15', '16'], ['*', '21', '30'], ['32', '*', '35'], ['50', '45', '*'], ['*', '51', '58'], ['64', '70', '*'], ['73', '*', '78'], ['*', '*', '*']], [['*', '*', '10'], ['*', '11', '17'], ['29', '23', '26'], ['*', '*', '32'], ['47', '41', '45'], ['53', '*', '52'], ['*', '*', '*'], ['73', '74', '77'], ['*', '*', '*']]], 2: [[['*', '10', '4'], ['20', '13', '*'], ['*', '28', '24'], ['*', '37', '*'], ['*', '47', '48'], ['56', '*', '58'], ['67', '*', '70'], ['78', '*', '*'], ['85', '*', '90']], [['*', '*', '7'], ['18', '15', '11'], ['22', '26', '*'], ['33', '*', '*'], ['49', '*', '50'], ['57', '*', '*'], ['64', '69', '66'], ['*', '*', '76'], ['84', '*', '85']], [['6', '*', '*'], ['20', '*', '17'], ['28', '23', '*'], ['31', '34', '36'], ['*', '*', '43'], ['53', '*', '54'], ['65', '64', '*'], ['*', '79', '*'], ['90', '83', '86']]]}

# net = Network("192.168.1.9", 9999)

# data = net.game.serialize_cards(mydict)
# print(net.game.deserialize_cards(data))