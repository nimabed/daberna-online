import sys
import asyncio
import pygame

from rects import Rects
from setting import *
from network import Network
from serialization import GameSerialization


pygame.init()
clock = pygame.time.Clock()


class Client:
    def __init__(self, ip, port, name, cards_num):
        self.ip = ip
        self.port = port
        self.cards_num = cards_num
        self.name = name

        # Network setup
        self.net = None
        self.p_id = None
        self.number_of_players = None
        
        # Games variables
        self.game_state = None
        self.cards = None
        self.game_rects = None
        self.get_pos = None
        self.reset_button = False
        self.marked_rects = []
        self.result_visible = False
        self.flash_period = 1000
        self.lock = asyncio.Lock()
        self.stop_event = True
        # self.stop_event = asyncio.Event()
        self.last_time = pygame.time.get_ticks()

        # Screen
        self.width = 1248
        self.height = 692

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Daberna')

        # Font setup
        self.game_font = pygame.font.SysFont("FreeSerif", 30)
        self.opponent_font = pygame.font.SysFont("FreeSerif", 25)
        self.random_num_font = pygame.font.SysFont("Lato Black", 70)

    async def network_init(self):
        self.net = Network(self.ip, self.port)
        players_info = await self.net.connect()
        self.p_id = int(players_info[0])
        self.number_of_players = int(players_info[1])
        await self.net.send(f"{self.name}:{self.cards_num}")

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
            
    async def rect_check(self):
        if self.get_pos:
            for i in range(len(self.game_rects[self.p_id])):
                for rect in self.game_rects[self.p_id][i]:
                    if rect.clicked(self.get_pos) and rect.text == str(self.game_state["rand_num"]):
                        self.marked_rects.append(rect)
                        await self.net.send(f"M{rect.text},{i}")
            self.get_pos = None

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
                text = self.game_font.render(self.game_state['players'][player], 1, (250,0,0))
                text_rect = text.get_rect(topleft=(10,5))
            else:
                [rect.draw_opponent(self.screen) for rects in cards for rect in rects]
                if self.number_of_players == 2:
                    text = self.opponent_font.render(self.game_state['players'][player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(10,477))
                elif self.number_of_players == 3:
                    select += 1
                    pos = (10, self.width/2+10)
                    text = self.opponent_font.render(self.game_state['players'][player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))
                elif self.number_of_players == 4:
                    select += 1
                    pos = (10,426,842)
                    text = self.opponent_font.render(self.game_state['players'][player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))
                else:
                    select += 1
                    pos = (10,322,634,946)
                    text = self.opponent_font.render(self.game_state['players'][player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))

            self.screen.blit(text, text_rect)

    def draw_marked_rects(self):
        if self.marked_rects:
            for rect in self.marked_rects:
                rect.draw_lines(self.screen)

    def draw_opponent_moves(self):
        for player, all_player_cards in self.game_rects.items():
            if player != self.p_id and self.game_state["moves"][player]:
                [rect.fill_rect(self.screen) for rect_list in all_player_cards for rect in rect_list if (rect.text, str(all_player_cards.index(rect_list))) in self.game_state["moves"][player]] 

    async def flash_result(self, text):
        # reset_text = self.game_font.render("Press space to reset...", 1, (0,0,0))
        # reset_text_rect = reset_text.get_rect(midbottom=(self.width/2, 462))
        # self.screen.blit(reset_text, reset_text_rect)

        current_time = pygame.time.get_ticks()
        if current_time - self.last_time > self.flash_period:
            self.result_visible = not self.result_visible
            self.last_time = pygame.time.get_ticks()

        if self.result_visible:
            self.screen.blit(text, (20, 432))
            self.screen.blit(text, (self.width-text.get_width()-20, 432))

    async def draw_result(self):
        if self.game_state["result"].count(1) == 1:
            idx = self.game_state["result"].index(1)
            if idx == self.p_id:
                text = self.game_font.render("You win", 1, (0,200,0))
            else:
                text = self.game_font.render(f"{self.game_state['players'][idx]} wins", 1, (0,200,0))
        
        elif self.game_state["result"].count(1) > 1:
            text = self.game_font.render("Game is tie", 1, (0,200,0))

        await self.flash_result(text)
        await self.stop()
               
    async def draw_random_num(self):
        text_num = self.random_num_font.render(str(self.game_state["rand_num"]), 1, (255,0,0))
        text_timer = self.game_font.render(f"({self.game_state['random_num_counter']+1}s)", 1, (0,0,0))
        text_timer_rect = text_timer.get_rect(midleft=(text_num.get_width(),text_num.get_height()/2))
        merged_surface = pygame.Surface((text_num.get_width()+text_timer.get_width(), max(text_num.get_height(),text_timer.get_height())))
        merged_surface.fill((255,255,255))
        merged_surface.blit(text_num, (0,0))
        merged_surface.blit(text_timer, text_timer_rect)
        merged_surface_rect = merged_surface.get_rect(midbottom=(self.width/2+20, 462))
        self.screen.blit(merged_surface, merged_surface_rect)

    def draw_start_counter(self):
        text1 = self.game_font.render(f"Starting in ", 1, (0,0,0))
        text2 = self.game_font.render(f"{self.game_state['start_counter']}s", 1, (255,0,0))
        merged_surface = pygame.Surface((text1.get_width()+text2.get_width(), max(text1.get_height(),text2.get_height())))
        merged_surface.fill((255,255,255))
        merged_surface.blit(text1, (0,0))
        merged_surface.blit(text2, (text1.get_width(),0))
        merged_surface_rect = merged_surface.get_rect(midbottom=(self.width/2, 462))
        self.screen.blit(merged_surface, merged_surface_rect)
        
    async def reset_request(self):
        while True:
            if not self.game_state['running'] and 1 in self.game_state['result']:
                num = await asyncio.to_thread(input, "Write the number of cards you need then press enter(1 to 6): ")

                if int(num) > 6 or int(num) < 1:
                    print("Number is invalid, try again..")
                
                else:
                    self.cards = None
                    self.reset_button = True
                    self.cards_num = int(num)
                    await self.net.send(num+"reset")
                    # print("Before response")
                    response = await self.net.send_reset()
                    # print("After response")
                    if response == b'start':
                        # self.stop_event.clear()
                        self.stop_event = True
                        asyncio.create_task(self.get_game())
                        # print("Game started again")
                        # break
                    else:
                        print(f"Can not receive reset response:{response}")
                    await asyncio.sleep(0.1)
                    return
            await asyncio.sleep(0.3)
            
    async def draw_reset(self):
        if self.reset_button:
            text = self.game_font.render("Waiting for opponents...", 1, (0,0,0))
            text_rect = text.get_rect(midbottom=(self.width/2,462))
        else:
            text = self.game_font.render("Press space to reset...", 1, (0,0,0))
            text_rect = text.get_rect(midbottom=(self.width/2,462))
        self.screen.blit(text, text_rect)
                                      
    async def run(self):

        connected = all(self.game_state["players"])

        if not connected:
            self.ready_state()

        elif connected and not self.game_state["running"] and 1 not in self.game_state["result"]:
            await self.get_cards()
            self.marked_rects.clear()
            self.draw_rects()
            self.draw_start_counter()
            
        else:
            self.draw_rects()
            if self.game_state["rand_num"]:
                self.reset_button = False 
                await self.draw_random_num()
                await self.rect_check()
            else:
                await self.draw_result()
                await self.draw_reset()
                # await self.stop()
            self.draw_marked_rects()
            self.draw_opponent_moves()
            

    async def stop(self):
        if not self.reset_button and 1 in self.game_state['result']:
            self.stop_event = False

    async def get_game(self):
        # print("INSIDE get game")
        # count = 0
        # print(f"stop_event variable:{self.stop_event}")
        while self.stop_event:
            try:
                game = await self.net.send("get")
                # count += 1
                # print(f"get SENT:{count}")
                if not game:
                    print("Can not get the game state!")
                    break
                else:
                    self.game_state = GameSerialization.deserialize(game)
                    

            except asyncio.IncompleteReadError as e:
                print(f"Getting game state error: {e}")
            
            await asyncio.sleep(0.1)
            # if 1 in self.game_state['result']:
            #             await asyncio.sleep(2)
            #             await self.stop()

        print(f'Game Stoped!')


    async def get_cards(self):
        if not self.cards:
            try:
                cards_data = await self.net.send("getcards")
                if not cards_data:
                    print(f"Can not get cards!")
                else:
                    # self.cards = await self.game_state.deserialize_cards(cards_data)
                    self.cards = GameSerialization.deserialize_cards(cards_data)
                    self.game_rects = self.cards_rects()
            except asyncio.IncompleteReadError as e:
                print(f"Getting cards error: {e}")

    async def handle_input(self):
        print("INSIDE handle input")
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.get_pos = pygame.mouse.get_pos()

                elif event.type == pygame.KEYDOWN:  
                    if event.key == pygame.K_SPACE:
                        if not self.reset_button:
                            asyncio.create_task(self.reset_request())

            await asyncio.sleep(0.01)

    async def update_display(self):
        print("INSIDE update display")
        while True:
            self.screen.fill((255,255,255))

            if self.game_state:
                await self.run()
            # else:
            #     print("NO GAME")

            pygame.display.update()
            clock.tick(60)

            await asyncio.sleep(0)

    async def run_game(self):
        asyncio.create_task(self.get_game())
        await asyncio.gather(self.handle_input(),
                             self.update_display())


 

    


