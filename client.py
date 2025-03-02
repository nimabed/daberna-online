import sys, threading
import asyncio
import pygame

from rects import Rects
from setting import *
from network import Network


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
                    if rect.clicked(self.get_pos) and rect.text == str(self.game_state.rand_num):
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
        if not self.game_rects:
            self.game_rects = self.cards_rects()

        self.draw_separate_lines()
        select = -1
        for player, cards in self.game_rects.items():
            if player == self.p_id:
                [rect.draw_player(self.screen) for rects in cards for rect in rects]
                text = self.game_font.render(self.game_state.players[player], 1, (250,0,0))
                text_rect = text.get_rect(topleft=(10,5))
            else:
                [rect.draw_opponent(self.screen) for rects in cards for rect in rects]
                if self.number_of_players == 2:
                    text = self.opponent_font.render(self.game_state.players[player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(10,477))
                elif self.number_of_players == 3:
                    select += 1
                    pos = (10, self.width/2+10)
                    text = self.opponent_font.render(self.game_state.players[player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))
                elif self.number_of_players == 4:
                    select += 1
                    pos = (10,426,842)
                    text = self.opponent_font.render(self.game_state.players[player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))
                else:
                    select += 1
                    pos = (10,322,634,946)
                    text = self.opponent_font.render(self.game_state.players[player], 1, (250,0,0))
                    text_rect = text.get_rect(topleft=(pos[select], 477))

            self.screen.blit(text, text_rect)

    def draw_marked_rects(self):
        if self.marked_rects:
            for rect in self.marked_rects:
                rect.draw_lines(self.screen)

    def draw_opponent_moves(self):
        for player, all_player_cards in self.game_rects.items():
            if player != self.p_id and self.game_state.moves[player]:
                [rect.fill_rect(self.screen) for rect_list in all_player_cards for rect in rect_list if (rect.text, str(all_player_cards.index(rect_list))) in self.game_state.moves[player]] 

    def flash_result(self, text):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time > self.flash_period:
            self.result_visible = not self.result_visible
            self.last_time = pygame.time.get_ticks()

        if self.result_visible:
            self.screen.blit(text, (20, 432))
            self.screen.blit(text, (self.width-text.get_width()-20, 432))

    def draw_result(self):
        if self.game_state.result.count(1) == 1:
            idx = self.game_state.result.index(1)
            if idx == self.p_id:
                text = self.game_font.render("You win", 1, (0,200,0))
            else:
                text = self.game_font.render(f"{self.game_state.players[idx]} wins", 1, (0,200,0))
        
        elif self.game_state.result.count(1) > 1:
            text = self.game_font.render("Game is tie", 1, (0,200,0))

        self.flash_result(text)
               
    async def draw_random_num(self):
        text_num = self.random_num_font.render(str(self.game_state.rand_num), 1, (255,0,0))
        text_timer = self.game_font.render(f"Timer: {self.game_state.random_num_counter+1}", 1, (0,0,0))
        text_num_rect = text_num.get_rect(midbottom=(100, 462))
        text_timer_rect = text_timer.get_rect(midbottom=(self.width-85, 462))
        self.screen.blit(text_num, text_num_rect)
        self.screen.blit(text_timer, text_timer_rect)

    async def draw_start_counter(self):
        text1 = self.game_font.render(f"Starting in ", 1, (0,0,0))
        text2 = self.game_font.render(f"{self.game_state.start_counter}s", 1, (255,0,0))
        merged_surface = pygame.Surface((text1.get_width()+text2.get_width(), max(text1.get_height(),text2.get_height())))
        merged_surface.fill((255,255,255))
        merged_surface.blit(text1, (0,0))
        merged_surface.blit(text2, (text1.get_width(),0))
        merged_surface_rect = merged_surface.get_rect(midbottom=(self.width-85, 462))
        self.screen.blit(merged_surface, merged_surface_rect)

    def retry_request(self):
        if not game.running and 1 in game.result and not self.reset_button:
            client.net.send("retry")
            self.reset_button = True

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
        
    async def reset_request(self):
        if not game.running and 1 in game.result and not self.reset_button:
            num = await asyncio.to_thread(input, "Write the number of cards you need then press enter(1 to 6): ")
            if 1 <= int(num) <= 6:
                self.cards_num = int(num)
                await self.net.send(num+"reset")
                self.cards = None
                self.reset_button = True

    def draw_reset(self):
        if self.reset_button:
            text = self.game_font.render("Waiting...", 1, (0,0,0))
            self.screen.blit(text, (20, 100))
        else:
            text = "Press space\nto RESET..."
            text_l = text.split("\n")
            y = 100
            for line in text_l:
                text = self.game_font.render(line, 1, (0,0,0))
                self.screen.blit(text, (20, y))
                y += self.game_font.get_linesize()


    async def run(self):
        if not await self.game_state.all_connected():
            self.draw_ready()
            # print("First Stage!")

        elif await self.game_state.all_connected() and not self.game_state.running and not 1 in self.game_state.result:
            # print("Second Stage!")
            await self.get_cards()
            self.draw_rects()
            await self.draw_start_counter()
            # print(self.cards)
            # if not self.cards:
            #     print("waitin for cards...")
            #     self.cards = await self.net.receive_cards()
            #     self.game_rects = self.cards_rects()
                
            # self.marked_rects.clear()
            

        else:
            self.draw_rects()
            if self.game_state.rand_num:
                self.reset_button = False
                await self.draw_random_num()
                await self.rect_check()
                # print(self.game_state.rand_num)
            else:
                self.draw_result()
                self.draw_reset()
            self.draw_marked_rects()
            self.draw_opponent_moves()


    async def get_game(self):
        # count_send = 0
        # count_receive = 0
        while True:
            try:
                game = await self.net.send_get("get")
                # count_send += 1
                if not game:
                    # print("Can not get game state!")
                    break
                else:
                    self.game_state = game
                    # count_receive += 1
                    # print(f"SENT:{count_send}  RECEIVED:{count_receive}")
                    
            except asyncio.IncompleteReadError as e:
                print(f"Getting game state error: {e}")

            await asyncio.sleep(0.01)

    async def get_cards(self):
        if not self.cards:
            try:
                cards_data = await self.net.send("getcards")
                if not cards_data:
                    print(f"Can not get cards!")
                else:
                    self.cards = await self.game_state.deserialize_cards(cards_data)
            except asyncio.IncompleteReadError as e:
                print(f"Getting cards error: {e}")

    async def handle_input(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.get_pos = pygame.mouse.get_pos()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.retry_request()
                        
                    elif event.key == pygame.K_SPACE:
                        # threading.Thread(target=client.reset_request).start()
                        asyncio.create_task(self.reset_request())
            await asyncio.sleep(0.01)

    async def update_display(self):
        while True:
            self.screen.fill((255,255,255))

            if self.game_state:
                await self.run()

            pygame.display.update()
            clock.tick(60)

            await asyncio.sleep(0)

    async def run_game(self):
        await asyncio.gather(self.get_game(),
                             self.handle_input(),
                             self.update_display())


async def main():
    user_name = input("Enter your name: ")                   
    client = Client("192.168.1.9", 9999, user_name, 4)
    await client.network_init()

    await asyncio.sleep(0.1)

    await client.run_game()




if __name__ == "__main__":
    asyncio.run(main())

    # while True:
        
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             pygame.quit()
    #             sys.exit()

    #         elif event.type == pygame.MOUSEBUTTONDOWN:
    #             client.get_pos = pygame.mouse.get_pos()

    #         elif event.type == pygame.KEYDOWN:
    #             if event.key == pygame.K_RETURN:
    #                 client.retry_request()
                    
    #             elif event.key == pygame.K_SPACE:
    #                 # threading.Thread(target=client.reset_request).start()
    #                 asyncio.create_task(client.reset_request())

            
    #     game = await client.get_game(2)

    #     client.screen.fill((255,255,255))   
    #     if game: 
    #         await client.run(game)
        
    #     pygame.display.update()
    #     clock.tick(60)

    


