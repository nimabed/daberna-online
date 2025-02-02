import socket, pickle, random, time, hashlib, struct
from _thread import *
from gctl import Game


class Server:
    def __init__(self, host, port, num_of_players):
        self.host = host
        self.port = port 
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind((self.host, self.port))
        except socket.error as e:
            print(f"Binding error: {e}")

        # Variables
        self.players = num_of_players
        self.game = Game(num_of_players)
        self.numbers = [i for i in range(1,91)]
        self.players_cards = {}
        self.clients = []

    def generate_card(self):
        card = []
        for i in range(9):
            card.append(random.sample(range(1 + i*10, 11 + i*10), 3))
        for _ in range(10):
            card[random.randint(0,8)][random.randint(0,2)] = "*"
        return [[str(item) for item in row]for row in card]
    
    def random_numbers(self):
        copy_counter = self.game.random_num_counter
        players_cards_bytes = self.game.serialize_cards(self.players_cards)
        checksum_cards = hashlib.sha256(players_cards_bytes).hexdigest()
        message_bytes = checksum_cards.encode()+players_cards_bytes
        message_length = len(message_bytes)
    
        time.sleep(0.2)
        for client in self.clients:
            try:
                client.sendall(struct.pack("I", message_length))
                client.sendall(message_bytes)
                time.sleep(0.1)
                # client.sendall(pickle.dumps(self.players_cards))
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
                    if 1 in self.game.result:
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
        
        self.game.players[player] = False
        self.game.running = False
        connection.close()
        print("Connection close!")

    def run(self):
        p_id = -1

        self.server.listen(self.players)
        print("listening...")

        while True:
            conn, addr = self.server.accept()
            p_id += 1
            conn.send(f"{p_id}:{self.players}".encode())
            self.clients.append(conn)
            print(f"Player {p_id} with address {addr} added!")
            
            try:
                data = conn.recv(1024)
                if not data:
                    print("Could not receive number of cards!")
                    break
                else:
                    name, cards_number = data.decode().split(":")
                    self.game.players[p_id] = name
                    self.players_cards[p_id] = [self.generate_card() for _ in range(int(cards_number))]
            except:
                pass

            if self.game.all_connected():
                start_new_thread(self.random_numbers, ())

            start_new_thread(self.active_client, (conn, p_id))


if __name__ == "__main__":
    server = Server("192.168.1.9", 9999, 3)
    server.run()



