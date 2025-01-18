import pygame, sys
from network import Network


pygame.init()
clock = pygame.time.Clock()

class Rects:
    def __init__(self, x, y, width, height, text):
        self.x = x
        self.y = y
        self.text = text
        self.width = width
        self.height = height

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
    def __init__(self, ip, port, cards_num):
        # Network setup
        self.cards_num = cards_num
        self.net = Network(ip, port)
        self.p_id = self.net.get_p()
        self.net.send(str(self.cards_num))
        
        # Games variables
        self.cards = None
        self.game_rects = None
        self.get_pos = None
        self.marked_rects = []
        if self.cards_num == 1:
            self.width = 790
            self.height = 600
            self.rect_size = 70
            self.offset_x = (80,)
            self.offset_y = (45,345)
        elif self.cards_num == 2:
            self.width = 1250
            self.height = 600
            self.rect_size = 60
            self.offset_x = (80,60*9+90)
            self.offset_y = (60,360)

        
        # Window setup
        # self.width = 800
        # self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Daberna')

        # Font setup
        self.game_font = pygame.font.SysFont(None, 40)
        self.font_in_rect = pygame.font.SysFont(None, 25)

    def ready_state(self):
        text = self.game_font.render("Waiting for connections....", 1, (0,0,0))
        text_rect = text.get_rect(center=(self.width/2, self.height/2))
        self.screen.blit(text, text_rect)
                
    def cards_rects(self):
        
        game_rects_dict = {}

        for player, card in self.cards.items():
            game_rects_list = []
            for i in range(len(card)):
                game_rects_list.append(self.generate_rects(card[i], self.offset_x[i], self.offset_y[player-1]))
            game_rects_dict[player] = game_rects_list
        return game_rects_dict
               
    def generate_rects(self, list, offset_x, offset_y):
        rect_card = []
        for row in range(9):
            for col in range(3):
                x = offset_x + row * self.rect_size
                y = offset_y + col * self.rect_size
                rect_card.append(Rects(x, y, self.rect_size, self.rect_size, list[row][col]))
        return rect_card
            
    def rect_check(self, number):
        if self.get_pos:
            for i in range(len(self.game_rects[self.p_id])):
                for rect in self.game_rects[self.p_id][i]:
                    if rect.clicked(self.get_pos) and rect.text == str(number):
                        self.marked_rects.append(rect)
                        self.net.send(f"{rect.text},{i}")

    def get_game(self, tries):
        counter = 0
        while counter <= tries:
            game = self.net.send("get")
            if game:
                return game
            else:
                counter += 1
        raise ValueError("Could not get game object")

    def draw_player_label(self):
        pygame.draw.line(self.screen, (0,0,0), (0,self.height/2), (self.width, self.height/2), 2)
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
        for i in range(len(self.game_rects)):
            for all_rects in self.game_rects[i+1]:
                [rect.draw(self.screen) for rect in [rects for rects in all_rects]]

    
    def draw_marked_rects(self):
        if self.marked_rects:
            for rect in self.marked_rects:
                rect.draw_lines(self.screen)

    def draw_opponent_moves(self):
        if game.p1_moves or game.p2_moves:
            if self.p_id == 1:
                rect_l = self.game_rects[2]
                opponent_moves = game.p2_moves
            else:
                rect_l = self.game_rects[1]
                opponent_moves = game.p1_moves
            for index, card in enumerate(rect_l):
                for rect in card:
                    if (rect.text,str(index)) in opponent_moves:
                        rect.draw_lines(self.screen)
                

    def draw_result(self):
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
        text_rect = text.get_rect(midbottom=(self.width/2, self.height/2))
        self.screen.blit(text, text_rect)

    def draw_start_counter(self, counter):
        text1 = self.game_font.render(f"Starting in ", 1, (0,0,0))
        text2 = self.game_font.render(f"{counter}s", 1, (255,0,0))
        merged_surface = pygame.Surface((text1.get_width()+text2.get_width(), max(text1.get_height(),text2.get_height())))
        merged_surface.fill((255,255,255))
        merged_surface.blit(text1, (0,0))
        merged_surface.blit(text2, (text1.get_width(),0))
        merged_surface_rect = merged_surface.get_rect(midbottom=(self.width/2,self.height/2))
        self.screen.blit(merged_surface, merged_surface_rect)

    def run(self, game):
        if not game.both_connected():
            self.draw_ready()

        elif game.both_connected and not game.running:
            if not self.cards:
                self.cards = self.net.receive_cards()
                self.game_rects = self.cards_rects()
            self.draw_rects()
            self.draw_start_counter(game.start_counter)

        else:
            self.draw_rects()
            if game.rand_num:
                self.draw_random_num(game.rand_num)
                self.rect_check(game.rand_num)
            else:
                self.draw_result()
            self.draw_marked_rects()
            self.draw_opponent_moves()
            
               
client = Client("192.168.1.9", 9999, 2)

    
while True:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            client.get_pos = pygame.mouse.get_pos()
        
    game = client.get_game(2)

    client.screen.fill((255,255,255))    
    client.run(game)
     
    pygame.display.update()
    clock.tick(60)
    
    

