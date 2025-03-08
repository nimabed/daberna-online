import asyncio
import game_pb2

class Game:
    def __init__(self, num_of_players):
        self.players = ["" for _ in range(num_of_players)]
        self.moves = [[] for _ in range(num_of_players)]
        self.result = [0 for _ in range(num_of_players)]
        self.players_num = num_of_players
        self.running = False
        self.reset_var = False
        self.rand_num = None
        self.start_counter = 4
        self.random_num_counter = 12
        self.lock = asyncio.Lock()


    async def all_connected(self):
        return all(self.players)   

    # Added with NARENJAK! :-)
    async def reset(self):
        async with self.lock:
            self.moves = [[] for _ in range(self.players_num)]
            self.result = [0 for _ in range(self.players_num)]
            self.start_counter = 4
            self.random_num_counter = 10
        
    async def player_move(self, p_id, number):
        self.moves[p_id].append(tuple(number.split(",")))

    async def winner_check(self, p_id, cards):
        check_list = self.moves[p_id]
        for index, card in enumerate(cards):
            for i in range(3):
                if [True for item in card if item[i].isdigit()] == [True for item in card if (item[i],str(index)) in check_list]:
                    self.result[p_id] = 1
                    return 



        
            
            

        
    

        
    
        
    
    

