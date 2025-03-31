import asyncio
from typing import Optional

class Game:
    def __init__(self, num_of_players: int) -> None:
        """
        Initialize game logic with the number of players.

        :param num_of_players: The number of players.
        """
        self.players: list[str] = ["" for _ in range(num_of_players)]
        self.moves: list[list[tuple[str,str]]] = [[] for _ in range(num_of_players)]
        self.result: list[int] = [0 for _ in range(num_of_players)]
        self.players_num: int = num_of_players
        self.running: bool = False
        self.reset_var: bool = False
        self.rand_num: Optional[int] = None
        self.start_counter: int = 4
        self.random_num_counter: int = 10
        self.lock: asyncio.Lock = asyncio.Lock()

    async def all_connected(self) -> bool:
        """
        Check if all players connected to server(Based on the number of players).

        :return: True if all players connected, False if all players not connected(Using builtin all module).
        """
        return all(self.players)   
    
    # Added with NARENJAK! :-)
    async def reset(self) -> None:
        """
        Reset some attributes to its default values when a game class created(Based on number of players).
        """
        async with self.lock:
            self.moves = [[] for _ in range(self.players_num)]
            self.result = [0 for _ in range(self.players_num)]
            self.start_counter = 4
            self.random_num_counter = 10
        
    async def player_move(self, p_id: int, move: str) -> None:
        """
        Set the player's move(The tuple including of the number that player has chosen and the card's number)to self.moves attribute(Based on player's id). 

        :param p_id: The player's id.
        :param move: The string of the number that player has chosen and the card's number separated by a comma. Exp: "24,1"
        """
        parts = move.split(",")
        if len(parts) != 2:
            raise ValueError(f"Invalid move format: {move}. Expected format: 'number,card_number'")
        t: tuple[str,str] = (parts[0], parts[1])
        self.moves[p_id].append(t)

    async def winner_check(self, p_id: int, cards: list[list[str]]) -> None:
        """
        Check all the cards(Rows by rows) that the player has(based on the player's moves).If 
        all the numbers in one row of a card were chosen by player then the value of the result
        attribute will change from 0 to 1(based on the player id).

        :param p_id: The player's id.
        :param cards: All the cards that the player has.
        :return: Nothing.
        """
        check_list = self.moves[p_id]
        for index, card in enumerate(cards):
            for i in range(3):
                if [True for item in card if item[i].isdigit()] == [True for item in card if (item[i],str(index)) in check_list]:
                    self.result[p_id] = 1
                    return None



        
            
            

        
    

        
    
        
    
    

