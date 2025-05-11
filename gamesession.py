import asyncio
import random
import hashlib
import struct
from serialization import GameSerialization
from dataclasses import dataclass, field
from gctl import Game
from typing import Dict, List

# Type aliases
Card = List[List[str]] 

@dataclass
class GameSession:
    player_nums: int

    game: Game = field(init=False)
    players_cards: Dict[int, List[Card]] = field(default_factory=dict)
    clients: List[asyncio.StreamWriter] = field(default_factory=list)
    try_var: int = 0
    number_of_sent_cards: int = 0
    lock: asyncio.Lock = asyncio.Lock()
    
    def __post_init__(self) -> None:
        self.game = Game(self.player_nums)

    def generate_card(self) -> Card:
        card: Card = []
        for i in range(9):
            card.append(random.sample(range(1 + i*10, 11 + i*10), 3))
        for _ in range(10):
            card[random.randint(0,8)][random.randint(0,2)] = "*"
        return [[str(item) for item in row]for row in card]
    
    async def retry_game(self) -> None:
        if self.try_var == self.player_nums and 1 in self.game.result:
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
            print(f"Cannot send player cards: {e}")

        if self.number_of_sent_cards == self.player_nums:
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
            if self.game.running and len(self.clients) == self.player_nums:
                num: int = random.choice(numbers)
                self.game.rand_num: int = num
                numbers.remove(num)
                for i in range(copy_counter):
                    self.game.random_num_counter -= 1
                    if 1 in self.game.result:
                        async with self.lock:
                            self.game.rand_num = None
                            self.game.running = False
                            self.try_var: int = 0
                            return None
                    await asyncio.sleep(1)
                self.game.random_num_counter: int = copy_counter
            elif self.try_var == self.player_nums:
                self.game.start_counter -= 1
                await asyncio.sleep(1.5)
                if self.game.start_counter == 0:
                    async with self.lock:
                        self.game.running = True
            else:
                break
    
    async def active_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, player_idx: int, sid:str) -> None:
        while True:
            try:
                raw_length: bytes = await reader.readexactly(4)
                if not raw_length:
                    print(f"Length not received, player_idx {player_idx} disconnected!")
                    break
                message_length: int = struct.unpack("I", raw_length)[0]
                raw_data: bytes = await reader.read(message_length)
                if not raw_data:
                    print(f"Player {player_idx} disconnected!")
                    break
                else:
                    data: str = raw_data.decode()
                    if data == "get":
                        async with self.lock:
                            await self.send_game(writer)
                    elif data.startswith("M"):
                        await self.game.player_move(player_idx, data[1:])
                        await self.game.winner_check(player_idx, self.players_cards[player_idx])
                    elif data.endswith("reset"):
                        async with self.lock:
                            self.try_var += 1
                            self.players_cards[player_idx] = [self.generate_card() for _ in range(int(data[0]))]

                            if self.try_var == self.player_nums:
                                await self.retry_game()
                    elif data == "getcards":
                        async with self.lock:
                            await self.send_cards(writer)
            except (asyncio.IncompleteReadError, BrokenPipeError) as e:
                print(f"Problem in receiving data from player {player_idx}: {e}") 
                break
        async with self.lock:
            self.game.players[player_idx] = ""
            self.clients.remove(writer)
            self.try_var -= 1
            self.game.running = False
            del self.players_cards[player_idx]
            writer.close()
            await writer.wait_closed()
        print(f"Player {player_idx}'s connection closed!")
        return sid, len(self.clients)
