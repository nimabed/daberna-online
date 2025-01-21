import socket, pickle, random, time, hashlib, struct
from _thread import *
from gctl import Game


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port 
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind((self.host, self.port))
        except socket.error as e:
            print(f"Binding error: {e}")

        # Variables
        self.game = Game()
        self.numbers = [i for i in range(1,91)]
        self.players_cards = {}
        self.clients = []

    def generate_card(self):
        card = []
        for i in range(9):
            card.append(random.sample(range(1 + i*10, 11 + i*10), 3))
        for _ in range(15):
            card[random.randint(0,8)][random.randint(0,2)] = "*"
        return [[str(item) for item in row]for row in card]
    
    def random_numbers(self):
        copy_counter = self.game.random_num_counter
    
        time.sleep(0.2)
        for client in self.clients:
            try:
                client.sendall(pickle.dumps(self.players_cards))
            except:
                print("Can not send players cards!")
                return

        while True:
            if self.game.running:
                num = random.choice(self.numbers)
                self.game.rand_num = num
                self.numbers.remove(num)
                for i in range(copy_counter):
                    self.game.random_num_counter -= 1
                    if self.game.result[0] or self.game.result[1]:
                        self.game.rand_num = None
                        return
                    time.sleep(1)
                self.game.random_num_counter = copy_counter
            else:
                self.game.start_counter -= 1
                time.sleep(2)
                if self.game.start_counter == 1:
                    self.game.running = True

    def active_client(self, connection, player):
        while True:
            try:
                raw_data = connection.recv(4096)
                if not raw_data:
                    print(f"Player {player} disconnected!")
                    break
                else:
                    data = raw_data.decode()
            
                    if data != "get":
                        self.game.player_move(player, data)
                        self.game.winner_check(player, self.players_cards[player])

                    else:
                        serialized_game = self.game.serialize()
                        checksum = hashlib.sha256(serialized_game).hexdigest()
                        message_bytes = checksum.encode()+serialized_game
                        message_length = len(message_bytes) 
                        connection.sendall(struct.pack("I", message_length))
                        connection.sendall(message_bytes)
                                
            except:
                pass
        
        if player == 1: self.game.p1 = False
        else: self.game.p2 = False
        self.game.running = False
        connection.close()
        print("Connection close!")

    def run(self):
        player = 0

        self.server.listen(2)
        print("listening...")

        while True:
            conn, addr = self.server.accept()
            player += 1
            self.clients.append(conn)
            conn.send(str(player).encode())
            print(f"Player {player} with address {addr} added!")

            try:
                data = conn.recv(1024)
                if not data:
                    print("Could not receive number of cards!")
                    break
                else:
                    cards_number = data.decode()
                    self.players_cards[player] = [self.generate_card() for _ in range(int(cards_number))]
            except:
                pass

            if player == 2:
                self.game.p1, self.game.p2 = True, True
                start_new_thread(self.random_numbers, ())

            start_new_thread(self.active_client, (conn, player))


if __name__ == "__main__":
    server = Server("192.168.1.9", 9999)
    server.run()



