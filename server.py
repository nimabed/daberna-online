import socket, pickle, random, time, hashlib
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


def random_numbers(game):
    global numbers

    while True:
        if game.both_ready():
            game.running = True
            num = random.choice(numbers)
            game.rand_num = num
            numbers.remove(num)
            time.sleep(2)
            if game.result[0] or game.result[1]:
                game.rand_num = None
                break
            time.sleep(3)
        
    
def active_client(connection, player, game):

    connection.send(str(player).encode())    

    while True:
        try:
            raw_data = connection.recv(4096)
            if not raw_data:
                print(f"Player {player} disconnected!")
                break
            else:
                data = raw_data.decode()
                if data == "ready" and not game.running:
                    response_data = players_card
                    connection.sendall(pickle.dumps(response_data))
                    
                elif data == "start":
                    if player == 1:
                        game.p1_ready = True
                    else:
                        game.p2_ready = True

                elif data != "get":
                    game.player_move(player, data)
                    game.winner_check(player, players_card[player])

                else:
                    serialized_game = game.serialize()
                    checksum = hashlib.sha256(serialized_game).hexdigest()
                    serialized_with_checksum = f"{checksum}:{serialized_game.decode()}".encode()
                    connection.sendall(serialized_with_checksum)
                             
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
players_card = {i:generate_card() for i in range(1,3)}
numbers = [i for i in range(1,91)]
clients = []

while True:
    conn, addr = server.accept()
    player += 1
    clients.append(conn)
    print(f"Player {player} with address {addr} added!")
    if player == 2:
        game.p1, game.p2 = True, True
        start_new_thread(random_numbers, (game,))

    start_new_thread(active_client, (conn, player, game))


