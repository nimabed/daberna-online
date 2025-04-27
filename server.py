import asyncio
import random
import hashlib
import struct
from gctl import Game
from serialization import GameSerialization
from typing import List, Optional, Dict

# Type aliases
Card = List[List[str]] 

class Server:
    def __init__(self, host: str, port: int, num_of_players: int) -> None:
        self.host: str = host
        self.port: int = port
        self.server: Optional[asyncio.Server] = None 

        # Variables
        self.players: int = num_of_players
        self.game: Game = Game(num_of_players)
        self.players_cards: Dict[int, List[Card]] = {}
        self.clients: List[asyncio.StreamWriter] = []
        self.try_var: int = 0
        self.number_of_sent_cards: int = 0
        self.lock: asyncio.Lock = asyncio.Lock()

    def generate_card(self) -> Card:
        card: Card = []
        for i in range(9):
            card.append(random.sample(range(1 + i*10, 11 + i*10), 3))
        for _ in range(10):
            card[random.randint(0,8)][random.randint(0,2)] = "*"
        return [[str(item) for item in row]for row in card]
    
    async def retry_game(self) -> None:
        if self.try_var == self.players and 1 in self.game.result:
            await self.game.reset()

            for client in self.clients:
                client.write('start'.encode())
                await client.drain()
                await asyncio.sleep(0.5)

    async def send_cards(self, client: asyncio.StreamWriter) -> None:
        players_cards_bytes: bytes = GameSerialization.serialize_cards(self.players_cards)
        checksum_cards: str = 'card' + hashlib.sha256(players_cards_bytes).hexdigest()
        message_bytes: bytes = checksum_cards.encode() + players_cards_bytes
        message_length: bytes = struct.pack("I", len(message_bytes))

        try:
            client.write(message_length + message_bytes)
            await client.drain()
            self.number_of_sent_cards += 1

        except Exception as e:
            print(f"Cannot send players cards: {e}")

        if self.number_of_sent_cards == self.players:
            await asyncio.sleep(0.1)
            asyncio.create_task(self.random_numbers())
            self.number_of_sent_cards: int = 0   
    
    async def send_game(self, client: asyncio.StreamWriter) -> None:        
        serialized_game: bytes = GameSerialization.serialize(self.game)
        checksum: str = 'game' + hashlib.sha256(serialized_game).hexdigest()
        message_bytes: bytes = checksum.encode() + serialized_game
        message_length: bytes = struct.pack("I", len(message_bytes))

        client.write(message_length+message_bytes)
        await client.drain()

    async def random_numbers(self) -> None:
        numbers: List[int] = [_ for _ in range(1,91)]
        copy_counter: int = self.game.random_num_counter

        while True:
            if self.game.running and len(self.clients) == self.players:
                num: int = random.choice(numbers)
                self.game.rand_num: int = num
                numbers.remove(num)
                for i in range(copy_counter):
                    self.game.random_num_counter -= 1
                    if 1 in self.game.result:
                        async with self.lock:
                            self.game.rand_num = None
                            self.game.running = False
                            self.reset: bool = True
                            return None
                    await asyncio.sleep(1)
                self.game.random_num_counter: int = copy_counter

            elif self.try_var == self.players:
                self.game.start_counter -= 1
                await asyncio.sleep(1.5)
                if self.game.start_counter == 0:
                    async with self.lock:
                        self.game.running = True
                        self.try_var: int = 0
                        
            else:
                break
            
    async def active_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, player: int) -> None:
        while True:
            try:
                raw_length: bytes = await reader.readexactly(4)
                if not raw_length:
                    print(f"Length not received, player {player} disconnected!")
                    break

                message_length: int = struct.unpack("I", raw_length)[0]

                raw_data: bytes = await reader.read(message_length)
                if not raw_data:
                    print(f"Player {player} disconnected!")
                    break
                else:
                    data: str = raw_data.decode()
                    if data == "get":
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
                print(f"Problem in receiving data from player {player}: {e}") 
                break
            

        async with self.lock:
            self.game.players[player] = ""
            self.clients.remove(writer)
            self.game.running = False
            writer.close()
            await writer.wait_closed()
        print(f"Player {player}'s connection closed!")

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr, port = writer.get_extra_info("peername")
        p_id: int = len(self.clients)
        
        self.clients.append(writer)
        self.try_var += 1

        writer.write(f"{p_id}:{self.players}".encode())
        await writer.drain()
        print(f"Player {p_id} with address {addr}:{port} added!")
        
        try:
            data_length_byte: bytes = await reader.readexactly(4)
            if not data_length_byte:
                print("Could not receive length of cards")

            message_length: int = struct.unpack("I", data_length_byte)[0]

            raw_data: bytes = await reader.read(message_length)
            if not raw_data:
                print("Could not receive number of cards!")
                return None
            else:
                name, cards_number = raw_data.decode().split(":")
                async with self.lock:
                    self.game.players[p_id] = name
                    self.players_cards[p_id] = [self.generate_card() for _ in range(int(cards_number))]
        except Exception as e:
            print(f"Error receiving initial data from player {p_id}: {e}")

        asyncio.create_task(self.active_client(reader, writer, p_id))

    async def run(self) -> None:
        try:
            self.server: Optional[asyncio.Server] = await asyncio.start_server(self.handle_connection, self.host, self.port)
        except Exception as e:
            print(f"Binding server error: {e}")

        print(f"Serving on {self.host}...")

        async with self.server:
            await self.server.serve_forever()


if __name__ == "__main__":
    server: Server = Server("192.168.1.9", 9999, 2)
    asyncio.run(server.run())





