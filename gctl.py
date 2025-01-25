import game_pb2

class Game:
    def __init__(self, num_of_players):
        self.players = [False for i in range(num_of_players)]
        self.moves = [[] for i in range(num_of_players)]
        self.result = [0 for i in range(num_of_players)]
        self.running = False
        self.rand_num = None
        self.start_counter = 4
        self.random_num_counter = 6
        # self.p2 = False
        # self.p1_ready = False
        # self.p2_ready = False
        # self.p2_moves = []

    def all_connected(self):
        return all(self.players)   

    def both_connected(self):
        return self.p1 and self.p2

    def both_ready(self):
        return self.p1_ready and self.p2_ready
    
    def player_move(self, p_id, number):
        self.moves[p_id].append(tuple(number.split(",")))

    def winner_check(self, p_id, cards):
        check_list = self.moves[p_id]

        for index, card in enumerate(cards):
            for i in range(3):
                if [True for item in card if item[i].isdigit()] == [True for item in card if (item[i], str(index)) in check_list]:
                    self.result[p_id] = 1
                    return 
            
    def serialize(self):
        game_proto = game_pb2.Game()
        game_proto.p1 = self.p1
        game_proto.p2 = self.p2
        game_proto.p1_ready = self.p1_ready
        game_proto.p2_ready = self.p2_ready
        game_proto.running = self.running
        game_proto.result.extend(self.result)
        game_proto.rand_num = self.rand_num if self.rand_num is not None else 0
        game_proto.start_counter = self.start_counter
        game_proto.random_num_counter = self.random_num_counter

        for move in self.p1_moves:
            p = game_proto.p1_moves.add()
            p.first, p.second = move

        for move in self.p2_moves:
            p = game_proto.p2_moves.add()
            p.first, p.second = move

        return game_proto.SerializeToString()

    def deserialize(self, data):
        game_proto = game_pb2.Game()
        game_proto.ParseFromString(data)
        self.p1 = game_proto.p1
        self.p2 = game_proto.p2
        self.p1_ready = game_proto.p1_ready
        self.p2_ready = game_proto.p2_ready
        self.running = game_proto.running
        self.result = list(game_proto.result)
        self.rand_num = game_proto.rand_num if game_proto.rand_num != 0 else None
        self.start_counter = game_proto.start_counter
        self.random_num_counter = game_proto.random_num_counter
        self.p1_moves = [(p.first, p.second) for p in game_proto.p1_moves]
        self.p2_moves = [(p.first, p.second) for p in game_proto.p2_moves]
            
            

        
    

        
    
        
    
    

