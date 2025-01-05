# from daberna1 import Daberna
import random, time, asyncio
# from queue import Queue

class Game:
    def __init__(self):
        self.p1 = False
        self.p2 = False
        self.p1win = False
        self.p2win = False
        self.tie = False
        self.running = False
        self.rand_nums = []

    def both_connected(self):
        return self.p1 and self.p2
    

    def get_rand_num(self):
        num = random.choice((self.numbers))
        self.rand_num.put(num)
        self.numbers.remove(num)
            

    def num_check(self):
        return self.p1_num == self.p2_num
    

        
    
        
    
    

