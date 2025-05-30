import asyncio
from client import Client


async def main() -> None:

    client: Client = Client("192.168.1.9", 9999)
    await asyncio.sleep(0.1)
    await client.run_game()
    


if __name__ == "__main__":
    asyncio.run(main())