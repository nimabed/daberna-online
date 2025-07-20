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
        self.handlers = {}
        self.listen = True

    def register_handler(self, name, func):
        self.handlers[name] = func

    async def message_dispatcher(self, byte_msg):
        if byte_msg.startswith(b'game'):
            handler = self.handlers.get('game')
            await handler(byte_msg[4:])
        elif byte_msg.startswith(b'card'):
            handler = self.handlers.get('cards')
            await handler(byte_msg[4:])
        elif byte_msg.startswith(b'start'):
            handler = self.handlers.get('reset')
            await handler(byte_msg)
        elif byte_msg.startswith(b'exit'):
            print("Received EXIT from server")
            handler = self.handlers.get('exit')
            await handler(byte_msg[4:])
            print(f"LISTEN IS: {self.listen}")
        else:
            handler = self.handlers.get('init')
            await handler(byte_msg)


    async def receiver(self):
        while self.listen:
            try:
                byte_length = await self.reader.readexactly(4)
                if not byte_length:
                    print("Can not receive the length of data")
                length = struct.unpack("I", byte_length)[0]
                byte_data = await self.reader.read(length)
                if not byte_data:
                    print("Can not receive the data")
                await self.message_dispatcher(byte_data)
            except asyncio.IncompleteReadError as e:
                print(f"Receiver error: {e}")
                # break
            await asyncio.sleep(0.1)

    async def connect(self, cmd: str, p_num_or_sid: int | str, cards: int, username: str) -> Optional[List[str]]:
        try:
            # Connecting..
            self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
            # Sending player's init info
            message: bytes = f"{cmd}:{p_num_or_sid}:{cards}:{username}".encode()
            length: bytes = struct.pack("I", len(message))
            self.writer.write(length+message)
            await self.writer.drain()
            self.listen = True
            asyncio.create_task(self.receiver())
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
        print("IN RESET METHOD")
        while True:
            data = await self.received_all()
            print(f"Received data: {data}")
            if data == b'start':
                return data
            
            await asyncio.sleep(0.3)

    async def send(self, data: str) -> Optional[bytes]:
        try:
            message: bytes = data.encode()
            length: bytes = struct.pack("I", len(message))
            self.writer.write(length+message)
            await self.writer.drain()
        except asyncio.IncompleteReadError as e:
            print(f"Sending error: {e}")
            return None
        return None
