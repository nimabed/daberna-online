import asyncio
import random
import hashlib
import struct
from gctl import Game

class Server:
    def __init__(self, host, port, num_of_players):
        self.host = host
        self.port = port
        self.server = None 

        # Variables
        self.players = num_of_players
        self.game = Game(num_of_players)
        self.players_cards = {}
        self.clients = {}
        self.try_var = 0
        self.number_of_sent_cards = 0
        self.reset = True
        self.lock = asyncio.Lock()

    def generate_card(self):
        card = []
        for i in range(9):
            card.append(random.sample(range(1 + i*10, 11 + i*10), 3))
        for _ in range(10):
            card[random.randint(0,8)][random.randint(0,2)] = "*"
        return [[str(item) for item in row]for row in card]
    
    async def retry_game(self):
        async with self.lock:
            if self.try_var == self.players and 1 in self.game.result:
                await self.game.reset()

    async def send_cards(self, client):
        async with self.lock:
            players_cards_bytes = await self.game.serialize_cards(self.players_cards)
            checksum_cards = hashlib.sha256(players_cards_bytes).hexdigest()
            message_bytes = checksum_cards.encode()+players_cards_bytes
            message_length = len(message_bytes)
            # print("Inside SEND CARDS... Sending cards")

            try:
                client.write(struct.pack("I", message_length))
                client.write(message_bytes)
                await client.drain()
                self.number_of_sent_cards += 1
            except Exception as e:
                print(f"Cannot send players cards: {e}")

            if self.number_of_sent_cards == self.players:
                await asyncio.sleep(0.1)
                asyncio.create_task(self.random_numbers())   

            # self.reset = False

    
    async def random_numbers(self):
        copy_counter = self.game.random_num_counter
        # print("Inside random numbers")

        while True:
            if self.game.running:
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
                            break
                    await asyncio.sleep(1)
                self.game.random_num_counter = copy_counter

            elif self.try_var == self.players:
                # await self.retry_game()
                # if self.reset:
                #     print("In RESET position")
                #     await asyncio.sleep(3)
                #     await self.send_cards()
    
                self.game.start_counter -= 1
                await asyncio.sleep(2)
                if self.game.start_counter == 1:
                    numbers = [_ for _ in range(1,91)]
                    async with self.lock:
                        self.game.running = True
                        self.try_var = 0

    async def active_client(self, reader, writer, player):
        while True:
            try:
                raw_data = await reader.read(4096)

                if not raw_data:
                    print(f"Player {player} disconnected!")
                    break
                else:
                    data = raw_data.decode()

                    if data == "retry":
                        self.try_var += 1

                    elif data[1:] == "reset":
                        async with self.lock:
                            self.try_var += 1
                            self.players_cards[player] = [self.generate_card() for _ in range(int(data[0]))]

                    elif data == "getcards":
                        await self.send_cards(writer)
                        
                    elif data != "get":
                        print(f"Player {player} moved --> {data}")
                        await self.game.player_move(player, data)
                        await self.game.winner_check(player, self.players_cards[player])

                    else:
                        # async with self.lock:
                        serialized_game = await self.game.serialize()
                        checksum = hashlib.sha256(serialized_game).hexdigest()
                        message_bytes = checksum.encode()+serialized_game
                        message_length = len(message_bytes) 
                        writer.write(struct.pack("I", message_length))
                        writer.write(message_bytes)
                        await writer.drain()
                        # print(f"Game state sent to player {player}")        
            except (asyncio.IncompleteReadError, BrokenPipeError) as e:
                print(f"Error handling client {player}: {e}")
                break

        async with self.lock:
            self.game.players[player] = False
            self.game.running = False
            writer.close()
            await writer.wait_closed()
            del self.clients[writer]
        print("Connection close!")

    async def handle_connection(self, reader, writer):
        addr, port = writer.get_extra_info("peername")
        p_id = len(self.clients)

        async with self.lock:
            self.clients[writer] = p_id
            self.try_var += 1

        writer.write(f"{p_id}:{self.players}".encode())
        await writer.drain()
        print(f"Player {p_id} with address {addr}:{port} added!")
        
        try:
            data = await reader.read(1024)
            if not data:
                print("Could not receive number of cards!")
                return
            else:
                name, cards_number = data.decode().split(":")
                print(name)
                print(cards_number)
                async with self.lock:
                    self.game.players[p_id] = name
                    self.players_cards[p_id] = [self.generate_card() for _ in range(int(cards_number))]

        except Exception as e:
            print(f"Error receiving initial data from player {p_id}: {e}")

        if await self.game.all_connected():
            pass
            # print("Starting random numbers")
            # await asyncio.sleep(0.2)
            # asyncio.create_task(self.random_numbers())

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






        # p_id = -1

        # self.server.listen(self.players)
        # print("listening...")

        # while True:
        #     conn, addr = self.server.accept()
        #     p_id += 1
        #     self.try_var += 1
        #     conn.send(f"{p_id}:{self.players}".encode())
        #     self.clients.append(conn)
        #     print(f"Player {p_id} with address {addr} added!")
            
        #     try:
        #         data = conn.recv(1024)
        #         if not data:
        #             print("Could not receive number of cards!")
        #             break
        #         else:
        #             name, cards_number = data.decode().split(":")
        #             self.game.players[p_id] = name
        #             self.players_cards[p_id] = [self.generate_card() for _ in range(int(cards_number))]
        #     except:
        #         pass

        #     if self.game.all_connected():
        #         threading.Thread(target=self.random_numbers).start()

        #     threading.Thread(target=self.active_client, args=(conn,p_id)).start()


# if __name__ == "__main__":
#     server = Server("192.168.1.9", 9999, 2)
#     asyncio.run(server.run())
    # server.run()



