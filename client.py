import sys
import asyncio
import pygame
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any

from rects import Rects
from setting import *
from network import Network
from serialization import GameSerialization

# Type aliases
Card = List[List[str]]
Card_Rect = List[List[Rects]]

pygame.mixer.pre_init()
pygame.init()
clock: pygame.time.Clock = pygame.time.Clock()


class Client:
    def __init__(self, ip: str, port: int, name: str, cards_num: int) -> None:
        self.ip: str = ip
        self.port: int = port
        self.cards_num: int = cards_num
        self.name: str = name

        # Network setup
        self.net: Optional[Network] = None
        self.p_id: Optional[int] = None
        self.number_of_players: Optional[int] = None
        
        # Games variables
        self.game_state: Optional[Dict[str, Any]] = None
        self.cards: Optional[Dict[int, List[Card]]] = None
        self.game_rects: Optional[Dict[int, Card_Rect]] = None
        self.get_pos: Optional[Tuple[int, int]] = None
        self.reset_button: int = 0
        self.marked_rects: List[Rects] = []
        self.result_visible: bool = False
        self.flash_period: int = 1000
        self.counter: int = 3
        self.lock: asyncio.Lock = asyncio.Lock()
        self.stop_event: bool = True
        self.last_time: int = pygame.time.get_ticks()

        # Win check analyze
        self.cards_analyze: Optional[Tuple[Tuple[int, int, int], ...]] = None
        self.marked_rows: List[List[int]] = [[0, 0, 0] for _ in range(cards_num)]
        self.last_analyze: int = 0

        # Screen
        self.width: int = 1248
        self.height: int = 692
        self.screen: pygame.Surface = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Daberna')

        # Font setup
        self.game_font: pygame.font.Font = pygame.font.SysFont("FreeSerif", 30)
        self.opponent_font: pygame.font.Font = pygame.font.SysFont("FreeSerif", 25)
        self.random_num_font: pygame.font.Font = pygame.font.SysFont("Lato Black", 70)

        # Sound setup
        self.played: bool = False
        self.cd: Path = Path(__file__).parent.resolve()
        self.checked: pygame.mixer.Sound = pygame.mixer.Sound(str(self.cd / 'Soundeffects/checked.mp3'))
        self.wrong: pygame.mixer.Sound = pygame.mixer.Sound(str(self.cd / 'Soundeffects/wrong.wav'))
        self.win: pygame.mixer.Sound = pygame.mixer.Sound(str(self.cd / 'Soundeffects/win.wav'))
        self.lose: pygame.mixer.Sound = pygame.mixer.Sound(str(self.cd / 'Soundeffects/lose.mp3'))
        self.count3: pygame.mixer.Sound = pygame.mixer.Sound(str(self.cd / 'Soundeffects/count1.wav'))
        self.count1: pygame.mixer.Sound = pygame.mixer.Sound(str(self.cd / 'Soundeffects/count2.wav'))

    async def network_init(self) -> None:
        self.net = Network(self.ip, self.port)
        players_info = await self.net.connect()
        self.p_id = int(players_info[0])
        self.number_of_players = int(players_info[1])
        await self.net.send(f"{self.name}:{self.cards_num}")

    def ready_state(self) -> None:
        text = self.game_font.render("Waiting for connections....", 1, (0,0,0))
        text_rect = text.get_rect(center=(self.width/2, self.height/2))
        self.screen.blit(text, text_rect)
                
    def cards_rects(self) -> Dict[int, Card_Rect]:
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
               
    def generate_rects(self, list: Card, offset_x: int, offset_y: int, font_size: int, rect_size: int) -> List[Rects]:
        rect_card = []
        for row in range(9):
            for col in range(3):
                x = offset_x + row * rect_size
                y = offset_y + col * rect_size
                rect_card.append(Rects(x, y, rect_size, rect_size, list[row][col], font_size, col))
        return rect_card

    def card_analize(self, card: Card) -> Tuple[int, int, int]:
        l = []
        for i in range(3):
            count = 0
            for j in range(9):
                if card[j][i].isdigit():
                    count += 1
            l.append(count)
        return tuple(l)
        
    def win_chance(self, row: int, col: int) -> None:
        num_of_digit = self.cards_analyze[row][col]
        num_of_marked = self.marked_rows[row][col]
        number = round((num_of_marked/num_of_digit)*100)
        if number > self.last_analyze:
            self.last_analyze = number
        return None
        
    async def rect_check(self) -> None:
        if self.get_pos:
            for i in range(len(self.game_rects[self.p_id])):
                for rect in self.game_rects[self.p_id][i]:
                    if rect.clicked(self.get_pos) and rect.text == str(self.game_state["rand_num"]):
                        self.marked_rects.append(rect)
                        self.marked_rows[i][rect.row] += 1
                        self.win_chance(i, rect.row)
                        pygame.mixer.Sound.play(self.checked)
                        await self.net.send(f"M{rect.text},{i}")
                        self.get_pos = None
                        return None
            pygame.mixer.Sound.play(self.wrong)
            self.get_pos = None

    def draw_win_chance(self) -> None:
        if self.last_analyze < 100:
            text1 = self.game_font.render("Wining chance: ", 1, (0, 0, 0))
            text2 = self.game_font.render(f"{self.last_analyze}%", 1, (255, 0, 0))
            merged_surface = pygame.Surface((text1.get_width() + text2.get_width(), max(text1.get_height(), text2.get_height())))
            merged_surface.fill((255,255,255))
            merged_surface.blit(text1, (0,0))
            merged_surface.blit(text2, (text1.get_width(),0))
            merged_surface_rect = merged_surface.get_rect(topright=(self.width-10, 5))
            self.screen.blit(merged_surface, merged_surface_rect)

    def draw_separate_lines(self) -> None:
        pygame.draw.line(self.screen, (0,0,0), (0,472), (self.width, 472), 2)

        if self.number_of_players == 3:
            pygame.draw.line(self.screen, (0,0,0), (self.width/2, 472), (self.width/2, self.height), 2)

        elif self.number_of_players == 4:
            for i in range(1,3):
                pygame.draw.line(self.screen, (0,0,0), ((self.width/3)*i, 472), ((self.width/3)*i, self.height), 2)

        elif self.number_of_players == 5:
            for i in range(1,4):
                pygame.draw.line(self.screen, (0,0,0), ((self.width/4)*i, 472), ((self.width/4)*i, self.height), 2)
        
    def draw_rects(self) -> None:
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

    def draw_marked_rects(self) -> None:
        if self.marked_rects:
            for rect in self.marked_rects:
                rect.draw_lines(self.screen)

    def draw_opponent_moves(self) -> None:
        for player, all_player_cards in self.game_rects.items():
            if player != self.p_id and self.game_state["moves"][player]:
                [rect.fill_rect(self.screen) for rect_list in all_player_cards for rect in rect_list if (rect.text, str(all_player_cards.index(rect_list))) in self.game_state["moves"][player]] 

    async def flash_result(self, text: pygame.font.Font) -> None:
        reset_quit_t = self.game_font.render("Press SPACE to reset or Q to quit", 1, (0,0,0))
        reset_quit_t_rect = reset_quit_t.get_rect(midbottom=(self.width/2, 462))
        self.screen.blit(reset_quit_t, reset_quit_t_rect)

        current_time = pygame.time.get_ticks()
        if current_time - self.last_time > self.flash_period:
            self.result_visible = not self.result_visible
            self.last_time = pygame.time.get_ticks()

        if self.result_visible:
            self.screen.blit(text, (20, 432))
            self.screen.blit(text, (self.width-text.get_width()-20, 432))

    async def win_lose_sound(self) -> None:
        if not self.played:
            if self.game_state["result"].index(1) == self.p_id:
                pygame.mixer.Sound.play(self.win)
            else:
                pygame.mixer.Sound.play(self.lose)
            self.played = True

    async def draw_result(self) -> None:
        if not self.reset_button:
            if self.game_state["result"].count(1) == 1:
                idx = self.game_state["result"].index(1)
                if idx == self.p_id:
                    text = self.game_font.render("You win", 1, (0,200,0))
                else:
                    text = self.game_font.render(f"{self.game_state['players'][idx]} wins", 1, (0,200,0))
            
            elif self.game_state["result"].count(1) > 1:
                text = self.game_font.render("Game is tie", 1, (0,200,0))

            await self.flash_result(text)
            await self.win_lose_sound()
            await self.stop()
               
    async def draw_random_num(self) -> None:
        text_num = self.random_num_font.render(str(self.game_state["rand_num"]), 1, (255,0,0))
        text_timer = self.game_font.render(f"({self.game_state['random_num_counter']+1}s)", 1, (0,0,0))
        text_timer_rect = text_timer.get_rect(midleft=(text_num.get_width(),text_num.get_height()/2))
        merged_surface = pygame.Surface((text_num.get_width()+text_timer.get_width(), max(text_num.get_height(),text_timer.get_height())))
        merged_surface.fill((255,255,255))
        merged_surface.blit(text_num, (0,0))
        merged_surface.blit(text_timer, text_timer_rect)
        merged_surface_rect = merged_surface.get_rect(midbottom=(self.width/2+20, 462))
        self.screen.blit(merged_surface, merged_surface_rect)

    async def countdown_sound(self, num: int) -> None:
        if num == self.counter and self.counter >= 1:
            pygame.mixer.Sound.play(self.count3)
            self.counter -= 1
        elif num == self.counter and self.counter == 0:
            pygame.mixer.Sound.play(self.count1)
            self.counter -= 1

    async def draw_start_counter(self) -> None:
        countdown = self.game_state['start_counter']
        if countdown == 0:
            text3 = self.random_num_font.render("GO..", 1, (255,0,0))
            text3_rect = text3.get_rect(midbottom=(self.width/2, 462))
            self.screen.blit(text3, text3_rect)
        else:
            text1 = self.game_font.render(f"Starting in ", 1, (0,0,0))
            text2 = self.game_font.render(f"{countdown}s", 1, (255,0,0))
            merged_surface = pygame.Surface((text1.get_width()+text2.get_width(), max(text1.get_height(),text2.get_height())))
            merged_surface.fill((255,255,255))
            merged_surface.blit(text1, (0,0))
            merged_surface.blit(text2, (text1.get_width(),0))
            merged_surface_rect = merged_surface.get_rect(midbottom=(self.width/2, 462))
            self.screen.blit(merged_surface, merged_surface_rect)
        await self.countdown_sound(countdown)

    async def reset_request(self) -> None:
        self.reset_button += 1
        while True:
            if not self.game_state['running'] and 1 in self.game_state['result']:
                num = await asyncio.to_thread(input, "Write the number of cards you need then press enter(1 to 6): ")

                if int(num) > 6 or int(num) < 1:
                    print("Number is invalid, try again..")
                
                else:
                    self.cards = None
                    self.reset_button += 1
                    self.cards_num = int(num)
                    await self.net.send(num+"reset")
                    response = await self.net.send_reset()
                    if response == b'start':
                        self.counter = 3
                        self.last_analyze = 0
                        self.stop_event = True
                        self.played = False
                        asyncio.create_task(self.get_game())
                        break
                    else:
                        print(f"Can not receive reset response:{response}")
                    await asyncio.sleep(0.1)
                    return None
            await asyncio.sleep(0.3)
            
    async def draw_reset(self) -> None:
        if self.reset_button:
            if self.reset_button > 1:
                text = self.game_font.render("Waiting for opponents...", 1, (0,0,0))
            else:
                text = self.game_font.render("Enter the number of cards", 1, (0,0,0))
            text_rect = text.get_rect(midbottom=(self.width/2,462))
            self.screen.blit(text, text_rect)
                                  
    async def run(self) -> None:
        connected = all(self.game_state["players"])

        if not connected:
            self.ready_state()

        elif connected and not self.game_state["running"] and 1 not in self.game_state["result"]:
            await self.get_cards()
            self.marked_rects.clear()
            self.draw_rects()
            await self.draw_start_counter()
            self.reset_button = 0
            
        else:
            self.draw_rects()
            if self.game_state['rand_num']:
                await self.draw_random_num()
                await self.rect_check()
                self.draw_win_chance()
            else:
                await self.draw_result()
                await self.draw_reset()
            self.draw_marked_rects()
            self.draw_opponent_moves()
            
    async def stop(self) -> None:
        if not self.reset_button and 1 in self.game_state['result']:
            self.stop_event = False

    async def get_game(self) -> None:
        while self.stop_event:
            try:
                game = await self.net.send("get")
                if not game:
                    print("Can not get the game state!")
                    break
                else:
                    self.game_state = GameSerialization.deserialize(game)
            except asyncio.IncompleteReadError as e:
                print(f"Getting game state error: {e}")
            
            await asyncio.sleep(0.1)         

    async def get_cards(self) -> None:
        if not self.cards:
            try:
                cards_data = await self.net.send("getcards")
                if not cards_data:
                    print(f"Can not get cards!")
                else:
                    self.cards = GameSerialization.deserialize_cards(cards_data)
                    self.game_rects = self.cards_rects()
                    self.cards_analyze = tuple((self.card_analize(card) for card in self.cards[self.p_id]))
                    # print((self.cards_analyze)[0][0])
            except asyncio.IncompleteReadError as e:
                print(f"Getting cards error: {e}")

    async def handle_input(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.get_pos = pygame.mouse.get_pos()

                elif event.type == pygame.KEYDOWN:  
                    if event.key == pygame.K_SPACE:
                        if not self.reset_button and 1 in self.game_state['result']:
                            asyncio.create_task(self.reset_request())

                    if event.key == pygame.K_q:
                        if not self.reset_button and 1 in self.game_state['result']:
                            pygame.quit()
                            sys.exit()

            await asyncio.sleep(0.01)

    async def update_display(self) -> None:
        while True:
            self.screen.fill((255,255,255))

            if self.game_state:
                await self.run()

            pygame.display.update()
            clock.tick(60)
            await asyncio.sleep(0)

    async def run_game(self) -> None:
        asyncio.create_task(self.get_game())
        await asyncio.gather(self.handle_input(),
                             self.update_display())


 

    


