import pygame
from pathlib import Path
from queue import LifoQueue
from typing import List, Any, Optional, Tuple
from menuoption import TextButton, Box, Cursor, InputSpinner
from network import Network


class Menu:
    def __init__(self, width: int, height: int, ip: str, port: int) -> None:
        # Variables
        self.info: Optional[Tuple[str, int, Any, str]] = None
        self.p_id: int = None
        self.room: str = None
        self.p_num: int = None
        self.width: int = width
        self.height: int = height
        self.cd: Path = Path(__file__).parent.resolve()
        self.state_stack: LifoQueue = LifoQueue()
        self.current_state: str = "main"
        self.cursor: Cursor = Cursor()
        self.net: Network = Network(ip, port)
        self.run_game: bool = False
        self.create_error: Optional[str] = None
        
        # Font
        self.button_font: pygame.font.Font = pygame.font.Font(str(self.cd / 'fonts/8-BITWONDER.TTF'), 18)
        self.title_font: pygame.font.Font = pygame.font.Font(str(self.cd / 'fonts/8-BITWONDER.TTF'), 36)

        # Colors
        self.orange: Tuple[int, int, int] = (252, 143, 84)
        self.purple: Tuple[int, int, int] = (68, 34, 88)
        self.white: Tuple[int, int, int] = (255,255,255)
        self.black: Tuple[int, int, int] = (0,0,0)
        self.gray: Tuple[int, int, int] = (160,160,160)
        
        # Boxes
        self.create_boxes = self.create_group_menu()
        self.join_boxes = self.join_group_menu()
        self.boxes = tuple(Box(self.width/2, self.height/2 + i*1, 150, 30) for i in (-65, -15, 35))


    async def network_init(self, *args) -> None:
        self.info = args
        name, cards_num, players_or_sid, command = args
        data = await self.net.connect(command, players_or_sid, cards_num, name)
        if command.startswith('J'):
            if not int(data[0]):
                self.create_error = "Wrong Group ID"
                return 1
            elif int(data[0]) == 1:
                self.create_error = "Group has been occupied"
                return 1
            self.room = players_or_sid
            self.p_num = int(data[0])
            self.p_id = int(data[1])
        else:
            self.room = data[0]
            self.p_id = int(data[1])

    def reset_boxes(self) -> None:
        self.create_error, self.info = None, None
        for box in (self.create_boxes[0], self.join_boxes[0], self.join_boxes[2]):
            box.text = ''

    def back_button(self) -> TextButton:
        return TextButton('back', self.button_font, self.orange, 60, 40)

    def main_menu(self) -> Tuple[TextButton, TextButton]:
        create_group: TextButton = TextButton('create group', self.button_font, self.orange, self.width/2, self.height/2)
        join_group: TextButton = TextButton('join group', self.button_font, self.orange, self.width/2, self.height/2+40)
        return create_group, join_group

    def create_group_menu(self) -> Tuple[Box, InputSpinner, InputSpinner, TextButton, TextButton, TextButton, TextButton]:
        name_text = TextButton('name', self.button_font, self.orange, self.width/2-200, self.height/2-40)
        name_box = Box(self.width/2, self.height/2 - 65, 150, 30)
        cards_text = TextButton('number of cards', self.button_font, self.orange, self.width/2-200, self.height/2)
        cards_box = InputSpinner(self.width/2, self.height/2 - 15, 150, 30)
        players_text = TextButton('number of players', self.button_font, self.orange, self.width/2-200, self.height/2+40)
        players_box = InputSpinner(self.width/2, self.height/2 + 35, 150, 30)
        players_box.var = 2
        create = TextButton('CREATE', self.button_font, self.white, self.width/2, self.height-150)
        return name_box, cards_box, players_box, create, name_text, cards_text, players_text

    def join_group_menu(self) -> Tuple[Box, InputSpinner, Box, TextButton, TextButton, TextButton, TextButton]:
        name_text = TextButton('name', self.button_font, self.orange, self.width/2-200, self.height/2-40)
        name_box = Box(self.width/2, self.height/2 - 65, 150, 30)
        cards_text = TextButton('number of cards', self.button_font, self.orange, self.width/2-200, self.height/2)
        cards_box = InputSpinner(self.width/2, self.height/2 - 15, 150, 30)
        group_id_text = TextButton('group id', self.button_font, self.orange, self.width/2-200, self.height/2+40)
        group_id_box = Box(self.width/2, self.height/2 + 35, 150, 30)
        join = TextButton('JOIN', self.button_font, self.white, self.width/2, self.height-150)
        return name_box, cards_box, group_id_box, join, name_text, cards_text, group_id_text

    def show_error(self) -> Tuple[pygame.Surface, pygame.Rect]:
        font = pygame.font.SysFont(None, 20)
        t = font.render(self.create_error, 1, self.gray)
        t_rect = t.get_rect(midbottom=(self.width/2, self.height-200))
        return t, t_rect
        
    async def create_button(self, pos: Tuple[int, int]) -> None:
        # Authorization error handling
        if self.create_boxes[3].clicked(pos):
            name, cards_num, p_num_or_sid, command = self.create_boxes[0].text, self.create_boxes[1].var, self.create_boxes[2].var, self.create_boxes[3].text
            if len(name) < 2:
                self.create_error = "Name must be at least 2 characters!"
                return None
            if not await self.network_init(name, cards_num, p_num_or_sid, command):
                self.run_game = True

    async def join_button(self, pos: Tuple[int, int]) -> None:
        # Authorization error handling
        if self.join_boxes[3].clicked(pos):
            name, cards_num, p_num_or_sid, command = self.join_boxes[0].text, self.join_boxes[1].var, self.join_boxes[2].text, self.join_boxes[3].text
            if len(name) < 2:
                self.create_error = "Name must be at least 2 characters!"
                return None
            if not await self.network_init(name, cards_num, p_num_or_sid, command):
                self.run_game = True

    async def draw_back_button(self, win: pygame.Surface) -> None:
        self.back_button().draw(win)

    async def draw_main_menu(self, win: pygame.Surface) -> None:
        title: pygame.Surface = self.title_font.render('main menu', 1, self.orange)
        title_rect: pygame.Rect = title.get_rect(midbottom=(self.width/2, 200))
        win.blit(title, title_rect)
        for item in self.main_menu():
            item.draw(win)

    async def draw_create_menu(self, win: pygame.Surface) -> None:
        title: pygame.Surface = self.title_font.render('create group', 1, self.orange)
        title_rect: pygame.Rect = title.get_rect(midbottom=(self.width/2, 200))
        win.blit(title, title_rect)
        if self.create_error: win.blit(*self.show_error())
        for item in self.create_boxes:
            item.draw(win)

    async def draw_join_menu(self, win: pygame.Surface) -> None:
        title: pygame.Surface = self.title_font.render('join group', 1, self.orange)
        title_rect: pygame.Rect = title.get_rect(midbottom=(self.width/2, 200))
        win.blit(title, title_rect)
        if self.create_error: win.blit(*self.show_error())
        for item in self.join_boxes:
            item.draw(win)

    async def draw_input_text(self, win: pygame.Surface) -> None:
        for box in (self.create_boxes[0], self.join_boxes[0], self.join_boxes[2]):
            win.blit(box.t_surf(), (box.x + 5, box.y + 5))

    def spin_click_check(self, spin_boxes: List[InputSpinner], pos: Tuple[int, int]) -> None:
        for i, spinbox in enumerate(spin_boxes):
                if not i:
                    if spinbox.up(pos) and spinbox.var < 4:
                        spinbox.var += 1
                    elif spinbox.down(pos) and spinbox.var > 1:
                        spinbox.var -= 1
                else:
                    if spinbox.up(pos) and spinbox.var < 4:
                        spinbox.var += 1
                    elif spinbox.down(pos) and spinbox.var > 2:
                        spinbox.var -= 1

    async def state_manager(self, pos: Tuple[int, int]) -> None:
        if not self.state_stack.empty() and self.back_button().clicked(pos):
            self.current_state = self.state_stack.get()
            return None
        if self.current_state == 'main':
            self.reset_boxes()
            self.cursor.active = False
            for option in self.main_menu():
                if option.clicked(pos):
                    self.state_stack.put(self.current_state)
                    self.current_state = option.text
                    break
        elif self.current_state == 'create group':
            self.cursor.pos(self.create_boxes[:1], pos)
            self.spin_click_check(self.create_boxes[1:3], pos)
            await self.create_button(pos)
        elif self.current_state == 'join group':
            self.cursor.pos((self.join_boxes[0], self.join_boxes[2]), pos)
            self.spin_click_check((self.join_boxes[1],), pos)
            await self.join_button(pos)
            
    async def draw(self, win: pygame.Surface) -> None:
        if not self.state_stack.empty():
            await self.draw_back_button(win)
        if self.current_state == 'main':
            await self.draw_main_menu(win)
        elif self.current_state == 'create group':
            await self.draw_create_menu(win)
            await self.draw_input_text(win)
            await self.cursor.draw(win)
        elif self.current_state == 'join group':
            await self.draw_join_menu(win)
            await self.draw_input_text(win)
            await self.cursor.draw(win)



        
        