
class Game:
    def __init__(self):
        self.p1 = False
        self.p2 = False
        self.p1_ready = False
        self.p2_ready = False
        self.running = False
        self.result = [0,0]
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
            
            

        
    

        
    
        
    
    

