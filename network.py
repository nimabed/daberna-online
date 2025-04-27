import asyncio
import hashlib
import struct
from typing import List, Optional

class Network:
    def __init__(self, ip: str, port: int) -> None:
        self.ip: str = ip
        self.port: int = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.lock: asyncio.Lock = asyncio.Lock()

    async def connect(self) -> Optional[List[str]]:
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        try:
            data: bytes = await self.reader.read(1024)
            return data.decode().split(":")
        except asyncio.IncompleteReadError as e:
            print(f"Connection error: {e}")
            return None 

    async def check_seri(self, check_game_byte: bytes) -> bool:
        received_checksum: str = hashlib.sha256(check_game_byte[68:]).hexdigest()
        return received_checksum.encode() == check_game_byte[4:68]

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

    async def send_card(self) -> Optional[bytes]:
        data_recv: Optional[bytes] = await self.received_all()
        if await self.check_seri(data_recv):
            return data_recv[68:]
        return None

    async def send_game(self) -> Optional[bytes]:
        data_recv: Optional[bytes] = await self.received_all()
        if await self.check_seri(data_recv):
            return data_recv[68:]
        return None

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
