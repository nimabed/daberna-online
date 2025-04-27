import asyncio
from client import Client

async def main() -> None:
    while True:
        user_name: str = input("Enter your name: ")
        if len(user_name) <= 1:
            print("Name must contain at least 2 characters!")
        else:
            break               
    client: Client = Client("192.168.1.9", 9999, user_name, 4)
    await client.network_init()
    await asyncio.sleep(0.1)
    await client.run_game()



if __name__ == "__main__":
    asyncio.run(main())