import asyncio
import random
import struct
from string import ascii_uppercase
from typing import List, Optional, Dict, Tuple, Any
from gamesession import GameSession
from datetime import datetime

# Type aliases
Card = List[List[str]]
Session = Dict[str, Any] 

class Server:
    def __init__(self, host: str, port: int) -> None:
        self.host: str = host
        self.port: int = port
        self.server: Optional[asyncio.Server] = None
        self.sessions :Dict[str, Session] = {}
        
    async def create_sid(self, char_num: int) -> str:
        sid: List[str] = random.choices(ascii_uppercase, k=char_num)
        return ''.join(sid)

    async def create_session(self, player_num: int) -> Tuple[str, int]:
        while True:
            session_id = await self.create_sid(4)
            if session_id not in self.sessions:
                self.sessions[session_id] = {"id": session_id,
                                             "game_session": GameSession(player_num),
                                             "max_members": player_num,
                                             "current_members": 0,
                                             "created": datetime.now().replace(microsecond=0)}
                
                return session_id, 0

    async def join_session(self, writer: asyncio.StreamWriter, session: Dict[str, Any], cards: str, p_name: str) -> Tuple[int, int]:
        players: int = session["max_members"]
        p_id: int = session["current_members"]
        session["game_session"].clients.append(writer)
        session["game_session"].game.players[p_id] = p_name
        session["game_session"].players_cards[p_id] = [session["game_session"].generate_card() for _ in range(int(cards))]
        session["game_session"].try_var += 1
        session["current_members"] += 1
        return players, p_id
        
    async def remove_session(self, p_name: str, sid: str, p_nums: int) -> None:
        session: Dict[str, Any] = self.sessions[sid]
        session["current_members"] -= 1
        max : int = session['max_members']
        print(f"{p_name} left group {sid}, Current members: {session['current_members']} || Remaining: {max - session['current_members']}")
        if not p_nums:
            del self.sessions[sid]
            print(f"Session {sid} was deleted!")
            print(f"Number of active sessions: {len(self.sessions)}")

    def task_callback(self, task: asyncio.Task) -> None:
        result: Tuple[str, int] = task.result()
        name: str = task.get_name()
        asyncio.create_task(self.remove_session(name, *result))

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr, port = writer.get_extra_info("peername")
        print(f"Connected: {addr}:{port}")
        
        try:
            data_length_byte: bytes = await reader.readexactly(4)
            if not data_length_byte:
                print("Could not receive length of message")
            message_length: int = struct.unpack("I", data_length_byte)[0]
            raw_data: bytes = await reader.read(message_length)
            if not raw_data:
                print("Could not receive contexts of message!")
                return None
            else:
                session = None
                command, *parts = raw_data.decode().split(":")
                if command == "CREATE":
                    sid, user_id = await self.create_session(int(parts[0]))
                    session = self.sessions[sid]
                    session["game_session"].clients.append(writer)
                    session["game_session"].game.players[user_id] = parts[2]
                    session["game_session"].try_var += 1
                    session["current_members"] += 1
                    session["game_session"].players_cards[user_id] = [session["game_session"].generate_card() for _ in range(int(parts[1]))]
                    print(f"Group {sid} created by {parts[-1]}, Capacity: {session['max_members']}")
                    writer.write(f"{sid}:{user_id}".encode())
                    await writer.drain()       

                elif command == "JOIN" and parts[0] in self.sessions:
                    session = self.sessions[parts[0]]
                    if session["current_members"] == session["max_members"]:
                        print(f"Group {session['id']} has been occupied, Members: {session['current_members']}")
                        writer.write("0:0".encode())
                        await writer.drain()
                        return None
                    else:
                        players, user_id = await self.join_session(writer, session, *parts[1:])
                        print(f"{parts[-1]} added to {parts[0]}'s group, Remaining: {session['max_members'] - session['current_members']}")
                        writer.write(f"{players}:{user_id}".encode())
                        await writer.drain()
                else:
                    print("Unrecognized command!")
                    return None

        except Exception as e:
            print(f"Error receiving initial data from address {addr}:{port}")
            return None
        
        if session:
            task = asyncio.create_task(session["game_session"].active_client(reader, writer, user_id, session["id"]), name=parts[-1])
            task.add_done_callback(self.task_callback)

    async def run(self) -> None:
        try:
            self.server: Optional[asyncio.Server] = await asyncio.start_server(self.handle_connection, self.host, self.port)
        except Exception as e:
            print(f"Binding server error: {e}")

        print(f"Serving on {self.host}...")

        async with self.server:
            await self.server.serve_forever()


if __name__ == "__main__":
    server: Server = Server("192.168.1.9", 9999)
    asyncio.run(server.run())





