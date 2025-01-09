
class Game:
    def __init__(self):
        self.p1 = False
        self.p2 = False
        self.p1_ready = False
        self.p2_ready = False
        self.p1win = False
        self.p2win = False
        self.tie = False
        self.running = False
        self.rand_num = None
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
        
    

        
    
        
    
    

