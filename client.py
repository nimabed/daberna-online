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
            
    def rect_check(self, number):
        # self.screen.fill((255,255,255))
        if self.get_pos:
            for rect in self.game_rects[self.p_id-1]:
                if rect.clicked(self.get_pos) and rect.text == str(number):
                    self.marked_rects.append(rect)
                    self.net.send(rect.text)

    def draw_player_label(self):
        if self.p_id == 1:
            you_text = self.game_font.render("You", 1, (255,0,0))
            you_text_rect = you_text.get_rect(topleft=(10,10))
            opponent_text = self.game_font.render("Opponent", 1, (255,0,0))
            opponent_text_rect = opponent_text.get_rect(topleft=(10,310))
            self.screen.blit(you_text, you_text_rect)
            self.screen.blit(opponent_text, opponent_text_rect)
        else:
            you_text = self.game_font.render("You", 1, (255,0,0))
            you_text_rect = you_text.get_rect(topleft=(10,310))
            opponent_text = self.game_font.render("Opponent", 1, (255,0,0))
            opponent_text_rect = opponent_text.get_rect(topleft=(10,10))
            self.screen.blit(you_text, you_text_rect)
            self.screen.blit(opponent_text, opponent_text_rect)

    def draw_ready(self):
        self.ready_state()
        
    def draw_rects(self):
        self.draw_player_label()
        for rects in self.game_rects:
            for rect in rects:
                rect.draw(self.screen)

    def draw_marked_rects(self):
        if self.marked_rects:
            for rect in self.marked_rects:
                rect.draw_lines(self.screen)

    def draw_opponent_moves(self):
        if game.p1_moves or game.p2_moves:
            if self.p_id == 1:
                rect_l = self.game_rects[1]
                opponent_moves = game.p2_moves
            else:
                rect_l = self.game_rects[0]
                opponent_moves = game.p1_moves
            for rect in rect_l:
                if rect.text in opponent_moves:
                    rect.draw_lines(self.screen)

    def result(self):
        if game.result[0] and game.result[1]:
            text = self.game_font.render("Game is tie", 1, (0,255,0))
            text_rect = text.get_rect(midbottom=(self.width/2,self.height/2))
            self.screen.blit(text, text_rect)

        elif self.p_id == 1 and game.result[0] and not game.result[1]:
            text = self.game_font.render("You Win", 1, (0,255,0))
            text_rect = text.get_rect(midbottom=(self.width/2,self.height/2))
            self.screen.blit(text, text_rect)

        elif self.p_id == 1 and not game.result[0] and game.result[1]:
            text = self.game_font.render("You Lose", 1, (0,255,0))
            text_rect = text.get_rect(midbottom=(self.width/2,self.height/2))
            self.screen.blit(text, text_rect)

        elif self.p_id == 2 and game.result[0] and not game.result[1]:
            text = self.game_font.render("You Lose", 1, (0,255,0))
            text_rect = text.get_rect(midbottom=(self.width/2,self.height/2))
            self.screen.blit(text, text_rect)

        elif self.p_id == 2 and not game.result[0] and game.result[1]:
            text = self.game_font.render("You Win", 1, (0,255,0))
            text_rect = text.get_rect(midbottom=(self.width/2,self.height/2))
            self.screen.blit(text, text_rect)        

    def draw_random_num(self, number):
        text = self.game_font.render(str(number), 1, (255,0,0))
        text_rect = text.get_rect(center=(self.width/2, self.height/2))
        self.screen.blit(text, text_rect)

    def run(self, game):
        if not game.both_connected():
            self.draw_ready()
        elif game.both_connected and not game.running:
            self.draw_rects()
            self.net.send("start")
        else:
            self.draw_rects()
            if game.rand_num:
                self.draw_random_num(game.rand_num)
            self.rect_check(game.rand_num)
            self.draw_marked_rects()
            self.draw_opponent_moves()
            self.result()
            
                
        

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
    client.run(game)
     
    pygame.display.update()
    clock.tick(60)
    
    

