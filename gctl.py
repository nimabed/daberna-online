import asyncio
from typing import List, Tuple, Optional

# Type aliases
Move = Tuple[str,str]
PlayersMoves = List[List[Move]]
Cards = List[List[str]]

class Game:
    def __init__(self, num_of_players: int) -> None:
        """
        Initialize game logic with the number of players.

        :param num_of_players: The number of players.
        :raises ValueError: If num_of_players is less than 2
        """
        if num_of_players < 2:
            raise ValueError("Number of players must be at least 2")
        
        self.players: List[str] = ["" for _ in range(num_of_players)]   # Player names/IDs  
        self.moves: PlayersMoves = [[] for _ in range(num_of_players)]  # player moves history
        self.result: List[int] = [0 for _ in range(num_of_players)]     # Game results(0 or 1)
        self.players_num: int = num_of_players                          # Total number of players
        self.running: bool = False                                      # Game running state
        self.reset_var: bool = False                                    # Reset flag
        self.rand_num: Optional[int] = None                             # Random number for game logic
        self.start_counter: int = 4                                     # Game start countdown
        self.random_num_counter: int = 10                               # Random numbers countdown
        self.lock: asyncio.Lock = asyncio.Lock()                        # Async lock for thread safety

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

        :param p_id: The player's id(Must be between 0 and num_of_players-1).
        :param move: Format: "number,card_number" (e.g., "24,1").
        :raises ValueError: If p_id is invalid or move format is incorrect.
        """
        if not 0 <= p_id < self.players_num:
            raise ValueError(f"Invalid player ID: {p_id}. Must be between 0 and {self.players_num-1}")

        parts: List[str] = move.split(",")
        if len(parts) != 2:
            raise ValueError(f"Invalid move format: {move}. Expected format: 'number,card_number'")
        m: Move = (parts[0], parts[1])
        self.moves[p_id].append(m)

    async def winner_check(self, p_id: int, cards: Cards) -> None:
        """
        Check cards for winnig condition.

        :param p_id: The player's id.
        :param cards: List of cards to check.
        :raise ValueError: If p_id is Invalid.
        """
        if not 0 <= p_id < self.players_num:
            raise ValueError(f"Invalid player ID: {p_id}. Must be between 0 and {self.players_num-1}")
        
        check_list: List[Move] = self.moves[p_id]
        for index, card in enumerate(cards):
            for i in range(3):
                if [True for item in card if item[i].isdigit()] == [True for item in card if (item[i],str(index)) in check_list]:
                    self.result[p_id] = 1
                    return None



        
            
            

        
    

        
    
        
    
    

