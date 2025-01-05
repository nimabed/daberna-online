import pygame, socket, pickle, sys, time
from network import Network


pygame.init()
clock = pygame.time.Clock()

class Rects:
    def __init__(self, x, y, text):
        self.x = x
        self.y = y
        self.text = text
        self.width = 70
        self.height = 70

    def draw(self, win):
        font = pygame.font.SysFont(None, 25)
        pygame.draw.rect(win, (0,0,255), (self.x, self.y, self.width, self.height), 2)
        num = font.render(self.text, 1, (0,0,0))
        win.blit(num, (self.x + self.width/2 - num.get_width()/2, self.y + self.height/2 - num.get_height()/2))
    
    def clicked(self, pos):
        if (self.x <= pos[0] <= self.x + self.width) and (self.y <= pos[1]<= self.y + self.height):
            return True
        else:
            return False

    def draw_lines(self, win):
        pygame.draw.line(win, (255,0,0), (self.x+10, self.y+10), (self.x+self.width-10, self.y+self.height-10), 3)
        pygame.draw.line(win, (255,0,0), (self.x+self.width-10,self.y+10), (self.x+10, self.y+self.height-10), 3) 


class Client:
    def __init__(self, ip, port):
        # Network setup
        self.net = Network(ip, port)
        self.p_id = self.net.get_p()
        
        # Games variable
        self.cards = self.get_cards()
        self.game_rects = self.cards_rects()
        self.marked_rects = []
        self.get_pos = None
        self.start_time = time.time()
        self.counter = 0

        # Window setup
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Daberna')

        # Font setup
        self.game_font = pygame.font.SysFont(None, 40)
        self.font_in_rect = pygame.font.SysFont(None, 25)

    def ready_state(self):
        text = self.game_font.render("Waiting for connections....", 1, (0,0,0))
        text_rect = text.get_rect(center=(self.width/2, self.height/2))
        self.screen.blit(text, text_rect)

    def get_cards(self):
        return self.net.send("ready")
                
    def cards_rects(self):
        game_rects = []
        for player, card in self.cards.items():
            if player == 1:
                offset_y = 45
            else:
                offset_y = 345
            game_rects.append(self.generate_rects(card, offset_y))
        return game_rects
               
    def generate_rects(self, list, offset_y):
        rect_card = []
        for row in range(9):
            for col in range(3):
                x = 85 + row * 70
                y = offset_y + col * 70
                rect_card.append(Rects(x, y, list[row][col]))
        return rect_card
            
    def rect_check(self):
        # self.screen.fill((255,255,255))
        if self.get_pos:
            for rect in self.game_rects[self.p_id-1]:
                if rect.clicked(self.get_pos):
                    self.marked_rects.append(rect)

    def draw_ready(self):
        # self.screen.fill((255,255,255))
        self.ready_state()
        # self.start_state()

    def draw_rects(self):
        for rects in self.game_rects:
            for rect in rects:
                rect.draw(self.screen)

    def draw_marked_rects(self):
        if self.marked_rects:
            for rect in self.marked_rects:
                rect.draw_lines(self.screen)

    def run(self):
        self.draw_rects()
        
    def print_rand_num(self, rand_list):
        current_time = time.time()
        if current_time - self.start_time >= 5:
            print(rand_list[self.counter])
            self.counter += 1
            self.start_time = current_time

            

client = Client("192.168.1.9", 9999)

    
while True:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            client.get_pos = pygame.mouse.get_pos()
        
    game = client.net.send("get")

    client.screen.fill((255,255,255))    
    if not game.both_connected():
        client.draw_ready()
    else:
        client.run()
        client.print_rand_num(game.rand_nums)

        # pygame.time.delay(4000)    
        client.rect_check()
        client.draw_marked_rects()
            

    pygame.display.update()
    clock.tick(60)
    
    

