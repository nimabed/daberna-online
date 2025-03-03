import asyncio
from client import Client

async def main():
    user_name = input("Enter your name: ")                   
    client = Client("192.168.1.9", 9999, user_name, 2)
    await client.network_init()

    await asyncio.sleep(0.1)

    await client.run_game()



if __name__ == "__main__":
    asyncio.run(main())