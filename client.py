import sys

import pygame

from setting import *
from network import Network


pygame.init()
clock = pygame.time.Clock()

class Rects:
    def __init__(self, x, y, width, height, text, text_size):
        self.x = x
        self.y = y
        self.text = text
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("Lato Black", text_size)

    def draw_player(self, win):
        # font = pygame.font.SysFont("Lato Black", self.text_size)
        pygame.draw.rect(win, (0,0,255), (self.x, self.y, self.width, self.height), 2)
        num = self.font.render(self.text, 1, (0,0,0))
        win.blit(num, (self.x + self.width/2 - num.get_width()/2, self.y + self.height/2 - num.get_height()/2))

    def draw_opponent(self, win):
        # font = pygame.font.SysFont("Lato Black", self.text_size)
        if self.text == "*":
            pygame.draw.rect(win, (0,0,255), (self.x, self.y, self.width, self.height))
        else:
            pygame.draw.rect(win, (0,0,255), (self.x, self.y, self.width, self.height), 2)
            num = self.font.render(self.text, 1, (0,0,0))
            win.blit(num, (self.x + self.width/2 - num.get_width()/2, self.y + self.height/2 - num.get_height()/2))
    
    def clicked(self, pos):
        if (self.x <= pos[0] <= self.x + self.width) and (self.y <= pos[1]<= self.y + self.height):
            return True
        else:
            return False

    def draw_lines(self, win):
        pygame.draw.line(win, (255,0,0), (self.x+10, self.y+10), (self.x+self.width-10, self.y+self.height-10), 3)
        pygame.draw.line(win, (255,0,0), (self.x+self.width-10,self.y+10), (self.x+10, self.y+self.height-10), 3) 

    def fill_rect(self, win):
        pygame.draw.rect(win, (0,240,0), (self.x, self.y, self.width, self.height))


class Client:
    def __init__(self, ip, port, name, cards_num):

        # Network setup
        self.cards_num = cards_num
        self.name = name
        self.net = Network(ip, port)
        self.p_id = self.net.get_p_id()
        self.number_of_players = self.net.get_num_of_p()
        self.net.send(f"{self.name}:{self.cards_num}")
        
        # Games variables
        self.cards = None
        self.game_rects = None
        self.get_pos = None
        self.reset_button = False
        self.marked_rects = []
        self.result_visible = False
        self.flash_period = 1000
        self.last_time = pygame.time.get_ticks()

        # Screen
        self.width = 1248
        self.height = 692

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Daberna')

        # Font setup
        self.game_font = pygame.font.SysFont("FreeSerif", 30)
        self.opponent_font = pygame.font.SysFont("FreeSerif", 25)
        self.random_num_font = pygame.font.SysFont("Lato Black", 55)

    def ready_state(self):
        text = self.game_font.render("Waiting for connections....", 1, (0,0,0))
        text_rect = text.get_rect(center=(self.width/2, self.height/2))
        self.screen.blit(text, text_rect)
                
    def cards_rects(self):
        game_rects_dict = {}
        select = -1
        for player, card in self.cards.items():
            player_rects_list = []
            
            if player == self.p_id:
                rect_size = 47
                font_size = 29
                offset_x = PLAYER_CARDS_OFFSET[self.cards_num][0]
                offset_y = PLAYER_CARDS_OFFSET[self.cards_num][1]

            else:
                select += 1
                rect_size = 20
                font_size = 10
                if self.number_of_players == 4 and len(card) > 4: rect_size, font_size = 17, 9
                elif self.number_of_players == 5: rect_size, font_size = 16, 8
                offset_x = OPPONENT_CARDS_OFFSET[self.number_of_players][len(card)][select][0]
                offset_y = OPPONENT_CARDS_OFFSET[self.number_of_players][len(card)][select][1]

            for i in range(len(card)):
                player_rects_list.append(self.generate_rects(card[i], offset_x[i], offset_y[i], font_size, rect_size))
            game_rects_dict[player] = player_rects_list
        return game_rects_dict
               
    def generate_rects(self, list, offset_x, offset_y, font_size, rect_size):
        rect_card = []
        for row in range(9):
            for col in range(3):
                x = offset_x + row * rect_size
                y = offset_y + col * rect_size
                rect_card.append(Rects(x, y, rect_size, rect_size, list[row][col], font_size))
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

    def draw_separate_lines(self):
        pygame.draw.line(self.screen, (0,0,0), (0,472), (self.width, 472), 2)

        if self.number_of_players == 3:
            pygame.draw.line(self.screen, (0,0,0), (self.width/2, 472), (self.width/2, self.height), 2)

        elif self.number_of_players == 4:
            for i in range(1,3):
                pygame.draw.line(self.screen, (0,0,0), ((self.width/3)*i, 472), ((self.width/3)*i, self.height), 2)

        elif self.number_of_players == 5:
            for i in range(1,4):
                pygame.draw.line(self.screen, (0,0,0), ((self.width/4)*i, 472), ((self.width/4)*i, self.height), 2)

    def draw_ready(self):
        self.ready_state()
        
    def draw_rects(self):
        self.draw_separate_lines()
        select = -1
        for player, cards in self.game_rects.items():
            if player == self.p_id:
                [rect.draw_player(self.screen) for rects in cards for rect in rects]
                text = self.game_font.render(game.players[player], 1, (250,0,0))
                text_rect = text.get_rect(topleft=(10,5))
            else:
                [rect.draw_opponent(self.screen) for rects in cards for rect in rects]
                if self.number_of_players == 2:
                    text = self.opponent_font.render(game.players[player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(10,477))
                elif self.number_of_players == 3:
                    select += 1
                    pos = (10, self.width/2+10)
                    text = self.opponent_font.render(game.players[player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))
                elif self.number_of_players == 4:
                    select += 1
                    pos = (10,426,842)
                    text = self.opponent_font.render(game.players[player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))
                else:
                    select += 1
                    pos = (10,322,634,946)
                    text = self.opponent_font.render(game.players[player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))

            self.screen.blit(text, text_rect)

    def draw_marked_rects(self):
        if self.marked_rects:
            for rect in self.marked_rects:
                rect.draw_lines(self.screen)

    def draw_opponent_moves(self):
        for player, all_player_cards in self.game_rects.items():
            if player != self.p_id and game.moves[player]:
                [rect.fill_rect(self.screen) for rect_list in all_player_cards for rect in rect_list if (rect.text, str(all_player_cards.index(rect_list))) in game.moves[player]] 

    def flash_result(self, text):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time > self.flash_period:
            self.result_visible = not self.result_visible
            self.last_time = pygame.time.get_ticks()

        if self.result_visible:
            self.screen.blit(text, (20, 432))
            self.screen.blit(text, (self.width-text.get_width()-20, 432))

    def draw_result(self):
        if game.result.count(1) == 1:
            idx = game.result.index(1)
            if idx == self.p_id:
                text = self.game_font.render("You win", 1, (0,200,0))
            else:
                text = self.game_font.render(f"{game.players[idx]} wins", 1, (0,200,0))
        
        elif game.result.count(1) > 1:
            text = self.game_font.render("Game is tie", 1, (0,200,0))

        self.flash_result(text)
               
    def draw_random_num(self, number, timer):
        text_num = self.random_num_font.render(str(number), 1, (255,0,0))
        text_timer = self.game_font.render(f"Timer: {timer+1}", 1, (0,0,0))
        text_num_rect = text_num.get_rect(midbottom=(100, 462))
        text_timer_rect = text_timer.get_rect(midbottom=(self.width-85, 462))
        self.screen.blit(text_num, text_num_rect)
        self.screen.blit(text_timer, text_timer_rect)

    def draw_start_counter(self, counter):
        text1 = self.game_font.render(f"Starting in ", 1, (0,0,0))
        text2 = self.game_font.render(f"{counter}s", 1, (255,0,0))
        merged_surface = pygame.Surface((text1.get_width()+text2.get_width(), max(text1.get_height(),text2.get_height())))
        merged_surface.fill((255,255,255))
        merged_surface.blit(text1, (0,0))
        merged_surface.blit(text2, (text1.get_width(),0))
        merged_surface_rect = merged_surface.get_rect(midbottom=(self.width-85, 462))
        self.screen.blit(merged_surface, merged_surface_rect)

    def retry_request(self):
        if not game.running and 1 in game.result and not self.reset_button:
            client.net.send("retry")

    def draw_retry(self):
        if self.reset_button:
            text = self.game_font.render("Waiting...", 1, (0,0,0))
            self.screen.blit(text, (self.width-150, 100))
        else:
            text = "Press enter\nto RETRY..."
            text_l = text.split("\n")
            y = 100
            for line in text_l:
                text = self.game_font.render(line, 1, (0,0,0))
                self.screen.blit(text, (self.width-150, y))
                y += self.game_font.get_linesize()
        # text_rect = text.get_rect(topleft=(self.width-text.get_width()-20, 100))
        

    def run(self, game):
        if not game.all_connected():
            self.draw_ready()

        elif game.all_connected and not game.running and not 1 in game.result:
            if not self.cards:
                self.cards = self.net.receive_cards()
                self.game_rects = self.cards_rects()
            self.marked_rects.clear()
            self.draw_rects()
            self.draw_start_counter(game.start_counter)

        else:
            self.draw_rects()
            if game.rand_num:
                self.reset_button = False
                self.draw_random_num(game.rand_num, game.random_num_counter)
                self.rect_check(game.rand_num)
            else:
                self.draw_result()
                self.draw_retry()
            self.draw_marked_rects()
            self.draw_opponent_moves()


user_name = input("Enter your name: ")            
            
client = Client("192.168.219.210", 9999, user_name, 4)

    
while True:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            client.get_pos = pygame.mouse.get_pos()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                client.retry_request()
                client.reset_button = True
        
    game = client.get_game(2)

    client.screen.fill((255,255,255))    
    client.run(game)
    
    pygame.display.update()
    clock.tick(60)

    
    

