import socket, pickle, random, time, hashlib, struct
from _thread import *
from gctl import Game


host = "192.168.1.9"
port = 9999


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.bind((host, port))
except socket.error as e:
    print(f"Bindig error: {e}")

def generate_card():
    card = []
    for i in range(9):
        card.append(random.sample(range(1 + i*10, 11 + i*10), 3))
    for _ in range(15):
        card[random.randint(0,8)][random.randint(0,2)] = "*"
    return [[str(item) for item in row]for row in card]


def random_numbers(game, clients):
    global numbers
    
    time.sleep(0.2)
    for client in clients:
        try:
            client.sendall(pickle.dumps(players_cards))
        except:
            print("Can not send players cards!")
            return

    while True:
        if game.running:
            num = random.choice(numbers)
            game.rand_num = num
            numbers.remove(num)
            for _ in range(5):
                if game.result[0] or game.result[1]:
                    game.rand_num = None
                    return
                time.sleep(1)
        else:
            game.start_counter -= 1
            time.sleep(2)
            if game.start_counter == 1:
                game.running = True
    
    
def active_client(connection, player, game):
   
    while True:
        try:
            raw_data = connection.recv(4096)
            if not raw_data:
                print(f"Player {player} disconnected!")
                break
            else:
                data = raw_data.decode()
        
                if data != "get":
                    game.player_move(player, data)
                    # game.winner_check(player, players_cards[player][0])

                else:
                    serialized_game = game.serialize()
                    checksum = hashlib.sha256(serialized_game).hexdigest()
                    message_bytes = checksum.encode()+serialized_game
                    message_length = len(message_bytes) 
                    connection.sendall(struct.pack("I", message_length))
                    connection.sendall(message_bytes)
                             
        except:
            pass

    if player == 1:
        game.p1 = False
    else:
        game.p2 = False
    game.running = False
    connection.close()
    print("Connection close!")
    

server.listen(2)
print("listening...")

player = 0
game = Game()
players_cards = {}
numbers = [i for i in range(1,91)]
clients = []

while True:

    conn, addr = server.accept()
    player += 1
    clients.append(conn)
    conn.send(str(player).encode())
    print(f"Player {player} with address {addr} added!")

    try:
        data = conn.recv(1024)
        if not data:
            print("Could not receive number of cards!")
            break
        else:
            cards_number = data.decode()
            players_cards[player] = [generate_card() for _ in range(int(cards_number))]

    except:
        pass

    if player == 2:
        game.p1, game.p2 = True, True
        start_new_thread(random_numbers, (game, clients))

    start_new_thread(active_client, (conn, player, game))


