import asyncio
from client import Client


async def main() -> None:
    while True:
        cmd: str = input("Enter command:(C/J) ").upper()
        username: str = input("Enter your name: ")
        cards: int = int(input("how many card do you want?(1-4) "))
        if cmd == "C":
            command = "CREATE"
            players_num : int = int(input("Enter players number:(2-4) "))
        elif cmd == "J":
            command = "JOIN"
            sid : str = input("Enter group ID: ")
        break

    client: Client = Client("192.168.1.9", 9999, cards, username)
    await client.network_init(command, players_num if cmd == "C" else sid)
    await asyncio.sleep(0.1)
    await client.run_game()


if __name__ == "__main__":
    asyncio.run(main())