import asyncio
import random
import hashlib
import struct
from gctl import Game
from serialization import GameSerialization

class Server:
    def __init__(self, host, port, num_of_players):
        self.host = host
        self.port = port
        self.server = None 

        # Variables
        self.players = num_of_players
        self.game = Game(num_of_players)
        self.players_cards = {}
        self.clients = []
        self.try_var = 0
        self.number_of_sent_cards = 0
        self.lock = asyncio.Lock()

    def generate_card(self):
        card = []
        for i in range(9):
            card.append(random.sample(range(1 + i*10, 11 + i*10), 3))
        for _ in range(10):
            card[random.randint(0,8)][random.randint(0,2)] = "*"
        return [[str(item) for item in row]for row in card]
    
    async def retry_game(self):
        # print("Inside retry game")
        if self.try_var == self.players and 1 in self.game.result:
            await self.game.reset()

            for client in self.clients:
                client.write('start'.encode())
                await client.drain()
                await asyncio.sleep(0.5)

    async def send_cards(self, client):
        players_cards_bytes = GameSerialization.serialize_cards(self.players_cards)
        checksum_cards = 'card' + hashlib.sha256(players_cards_bytes).hexdigest()
        message_bytes = checksum_cards.encode() + players_cards_bytes
        message_length = struct.pack("I", len(message_bytes))

        try:
            client.write(message_length + message_bytes)
            await client.drain()
            self.number_of_sent_cards += 1

        except Exception as e:
            print(f"Cannot send players cards: {e}")

        if self.number_of_sent_cards == self.players:
            await asyncio.sleep(0.1)
            asyncio.create_task(self.random_numbers())
            self.number_of_sent_cards = 0   
    
    async def send_game(self, client):        
        serialized_game = GameSerialization.serialize(self.game)
        checksum = 'game' + hashlib.sha256(serialized_game).hexdigest()
        message_bytes = checksum.encode() + serialized_game
        message_length = struct.pack("I", len(message_bytes))

        client.write(message_length+message_bytes)
        await client.drain()

    async def random_numbers(self):
        numbers = [_ for _ in range(1,91)]
        copy_counter = self.game.random_num_counter

        while True:
            if self.game.running and len(self.clients) == self.players:
                num = random.choice(numbers)
                self.game.rand_num = num
                numbers.remove(num)
                for i in range(copy_counter):
                    self.game.random_num_counter -= 1
                    if 1 in self.game.result:
                        async with self.lock:
                            self.game.rand_num = None
                            self.game.running = False
                            self.reset = True
                            return
                    await asyncio.sleep(1)
                self.game.random_num_counter = copy_counter

            elif self.try_var == self.players:
                self.game.start_counter -= 1
                await asyncio.sleep(2)
                if self.game.start_counter == 1:
                    async with self.lock:
                        self.game.running = True
                        self.try_var = 0
            else:
                break
            
    async def active_client(self, reader, writer, player):
        
        # count = 0
        while True:
            try:
                raw_length = await reader.readexactly(4)
                if not raw_length:
                    print(f"Length not received, player {player} disconnected!")

                message_length = struct.unpack("I", raw_length)[0]

                raw_data = await reader.read(message_length)
                if not raw_data:
                    print(f"Player {player} disconnected!")
                    break
                else:
                    data = raw_data.decode()
                    if data == "get":
                        # count += 1
                        # print(f"get RECEIVED:{count}")
                        async with self.lock:
                            await self.send_game(writer)

                    elif data.startswith("M"):
                        await self.game.player_move(player, data[1:])
                        await self.game.winner_check(player, self.players_cards[player])

                    elif data.endswith("reset"):
                        async with self.lock:
                            self.try_var += 1
                            self.players_cards[player] = [self.generate_card() for _ in range(int(data[0]))]

                            if self.try_var == self.players:
                                await self.retry_game()

                    elif data == "getcards":
                        async with self.lock:
                            await self.send_cards(writer)
                        
                        
            except (asyncio.IncompleteReadError, BrokenPipeError) as e:
                print(f"Error handling client {player}: {e}")
                break

        async with self.lock:
            self.game.players[player] = ""
            self.clients.remove(writer)
            self.game.running = False
            writer.close()
            await writer.wait_closed()
        print("Connection close!")

    async def handle_connection(self, reader, writer):
        addr, port = writer.get_extra_info("peername")
        p_id = len(self.clients)
        
        self.clients.append(writer)
        self.try_var += 1

        writer.write(f"{p_id}:{self.players}".encode())
        await writer.drain()
        print(f"Player {p_id} with address {addr}:{port} added!")
        
        try:
            data_length_byte = await reader.readexactly(4)
            if not data_length_byte:
                print("Could not receive length of cards")

            message_length = struct.unpack("I", data_length_byte)[0]

            raw_data = await reader.read(message_length)
            if not raw_data:
                print("Could not receive number of cards!")
                return
            else:
                name, cards_number = raw_data.decode().split(":")
                async with self.lock:
                    self.game.players[p_id] = name
                    self.players_cards[p_id] = [self.generate_card() for _ in range(int(cards_number))]
        except Exception as e:
            print(f"Error receiving initial data from player {p_id}: {e}")

        asyncio.create_task(self.active_client(reader, writer, p_id))

    async def run(self):
        try:
            self.server = await asyncio.start_server(self.handle_connection, self.host, self.port)
        except Exception as e:
            print(f"Binding server error: {e}")

        print(f"Serving on {self.host}...")

        async with self.server:
            await self.server.serve_forever()


if __name__ == "__main__":
    server = Server("192.168.1.9", 9999, 2)
    asyncio.run(server.run())





