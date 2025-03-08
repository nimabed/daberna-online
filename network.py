import asyncio
import hashlib
import struct

class Network:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.lock = asyncio.Lock()

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        try:
            data = await self.reader.read(1024)
            return data.decode().split(":")
        except asyncio.IncompleteReadError as e:
            print(f"Connection error: {e}")
            return 

    async def check_seri(self, check_game_byte):
        received_checksum = hashlib.sha256(check_game_byte[64:]).hexdigest()
        return received_checksum.encode() == check_game_byte[:64]

    async def received_message(self, count_byte):
        data_bytes = bytearray()
        while len(data_bytes) < count_byte:
            packet = await self.reader.read(count_byte - len(data_bytes))
            if not packet:
                return
            data_bytes.extend(packet)
        return bytes(data_bytes)
    
    async def received_all(self):
        async with self.lock:
            bytes_length = await self.received_message(4)
            if not bytes_length:
                return
            message_length = struct.unpack("I", bytes_length)[0]

            message_bytes = await self.received_message(message_length)
            if not message_bytes:
                return
        
        return message_bytes

    async def send(self, data):
        try:
            message = data.encode()
            length = struct.pack("I", len(message))
            self.writer.write(length+message)
            await self.writer.drain()

            if data == "getcards":
                data_recv = await self.received_all()
                if data_recv and await self.check_seri(data_recv):
                    return data_recv[64:]

        except asyncio.IncompleteReadError as e:
            print(f"Sending error: {e}")
            return

    async def send_get(self, data):
        try:
            message = data.encode()
            length = struct.pack("I", len(message))
            self.writer.write(length+message)
            await self.writer.drain()

            data_recv = await self.received_all()
            if not data_recv:
                print("Not receiving cards!")
            if await self.check_seri(data_recv):
                return data_recv[64:]
            else:
                print("Checksum mismatch!")
        except asyncio.IncompleteReadError as e:
            print(f"Sending error: {e}")
            return
