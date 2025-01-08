# from daberna1 import Daberna
import random, time, asyncio
# from queue import Queue

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
        self.number_request = False
        self.rand_num = None
            

    def both_connected(self):
        return self.p1 and self.p2
    

    # Adding both_ready method
    def both_ready(self):
        return self.p1_ready and self.p2_ready
    

    def get_rand_num(self):
        num = random.choice((self.numbers))
        self.rand_num.put(num)
        self.numbers.remove(num)
            

    def num_check(self):
        return self.p1_num == self.p2_num
    

        
    
        
    
    

