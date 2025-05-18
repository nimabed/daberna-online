import asyncio
import struct
from typing import List, Optional

class Network:
    def __init__(self, ip: str, port: int) -> None:
        self.ip: str = ip
        self.port: int = port
        self.writer: Optional[asyncio.StreamWriter] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.lock: asyncio.Lock = asyncio.Lock()

    async def connect(self, cmd: str, p_num_or_sid: int | str, cards: int, players: int) -> Optional[List[str]]:
        try:
            # Connecting..
            self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
            # Sending player's init info
            message: bytes = f"{cmd}:{p_num_or_sid}:{cards}:{players}".encode()
            length: bytes = struct.pack("I", len(message))
            self.writer.write(length+message)
            await self.writer.drain()
            # Receiving init player's data from server
            data: bytes = await self.reader.read(1024)
            return data.decode().split(":")
        except asyncio.IncompleteReadError as e:
            print(f"Connection error: {e}")
            return None 


    async def received_message(self, count_byte: int) -> Optional[bytes]:
        data_bytes: bytearray = bytearray()

        while len(data_bytes) < count_byte:
            packet: bytes = await self.reader.read(count_byte - len(data_bytes))
            if not packet:
                return None
            data_bytes.extend(packet)
            
        return bytes(data_bytes)
    
    async def received_all(self) -> Optional[bytes]:
        async with self.lock:
            bytes_length: Optional[bytes] = await self.received_message(4)
            if not bytes_length:
                return None
            message_length: int = struct.unpack("I", bytes_length)[0]

            message_bytes: Optional[bytes] = await self.received_message(message_length)
            if not message_bytes:
                return None
        
        return message_bytes

    async def send_card(self) -> bytes:
        data_recv: Optional[bytes] = await self.received_all()
        return data_recv[4:]

    async def send_game(self) -> bytes:
        data_recv: Optional[bytes] = await self.received_all()
        return data_recv[4:]

    async def send_reset(self) -> Optional[bytes]:
        async with self.lock:
            return await self.reader.read(512)

    async def send(self, data: str) -> Optional[bytes]:
        try:
            message: bytes = data.encode()
            length: bytes = struct.pack("I", len(message))
            self.writer.write(length+message)
            await self.writer.drain()

            if data == "getcards":
                return await self.send_card()
            
            elif data == "get":
                return await self.send_game()

        except asyncio.IncompleteReadError as e:
            print(f"Sending error: {e}")
            return None
        
        return None
