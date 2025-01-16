import game_pb2

class Game:
    def __init__(self):
        self.p1 = False
        self.p2 = False
        self.p1_ready = False
        self.p2_ready = False
        self.running = False
        self.result = [0,0]
        self.rand_num = None
        self.start_counter = 4
        self.p1_moves = []
        self.p2_moves = []
            

    def both_connected(self):
        return self.p1 and self.p2

    def both_ready(self):
        return self.p1_ready and self.p2_ready
    
    def player_move(self, p_id, number):
        if p_id == 1:
            self.p1_moves.append(number)
        else:
            self.p2_moves.append(number)

    def winner_check(self, p_id, card):
        if p_id == 1:
            check_list = self.p1_moves
        else:
            check_list = self.p2_moves
        for col in range(3):
            matched = 0
            temp = []
            for row in range(9):
                temp.append(card[row][col])
                if card[row][col] in check_list:
                    matched += 1
            if matched == sum([1 for i in temp if i.isdigit()]):
                self.result[p_id-1] = 1
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
        game_proto.p1_moves.extend(self.p1_moves)
        game_proto.p2_moves.extend(self.p2_moves)
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
        self.p1_moves = list(game_proto.p1_moves)
        self.p2_moves = list(game_proto.p2_moves)
            
            

        
    

        
    
        
    
    

