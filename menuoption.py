import pygame
from pathlib import Path
from typing import Tuple, Optional, Any

class TextButton:
    def __init__(self, text: str, font: pygame.font.Font, color: Tuple[int, int, int] , x: int, y: int) -> None:
        self.text = text
        self.x = x
        self.y = y
        self.t_surf = font.render(text, 1, color)
        self.t_surf_rect = self.t_surf.get_rect(midbottom=(self.x, self.y))
        
    def draw(self, win: pygame.Surface) -> None:
        win.blit(self.t_surf, self.t_surf_rect)

    def clicked(self, pos: Tuple[int, int]) -> bool:
        return self.t_surf_rect.collidepoint(pos)
    

class Box:
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Colors
        self.light_gray = (211,211,211)
        self.black = (0,0,0)
        self.text = ''
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, win: pygame.Surface) -> None:
        pygame.draw.rect(win, self.light_gray, self.rect)

    def clicked(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)
    
    def t_surf(self) -> pygame.Surface:
        font = pygame.font.SysFont(None, 25)
        return font.render(self.text, 1, self.black)


class Cursor:
    def __init__(self):
        font: pygame.font.Font = pygame.font.SysFont(None, 30)
        self.cursor_surf: pygame.Surface = font.render("|", 1, (0,0,0))
        self.cursor_rect: pygame.Rect = self.cursor_surf.get_rect()
        self.start: Optional[int] = None
        self.visible: bool = True
        self.period: int = 500
        self.active: bool = False 
        self.box: Optional[Tuple[int, Box]] = None

    def switch(self) -> None:
        if pygame.time.get_ticks() - self.start > self.period:
            self.visible = not self.visible
            self.start = pygame.time.get_ticks()

    async def draw(self, win: pygame.Surface) -> None:
        if self.active:
            self.cursor_rect.topleft = (self.box[1].x + 5 + self.box[1].t_surf().get_width(), self.box[1].y + 5)
            self.switch()
            if self.visible:
                win.blit(self.cursor_surf, self.cursor_rect)
        
    def pos(self, boxes: Optional[Any], pos: Tuple[int, int]) -> None:
        for i, box in enumerate(boxes):
            if box.clicked(pos):
                self.active = True
                self.start = pygame.time.get_ticks()
                self.box = (i, box)
                break
                

class InputSpinner:
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.cd = Path(__file__).parent.resolve()
        self.var = 1

        # Colors
        self.black = (0,0,0)
        self.gray = (211,211,211)
        
        self.font = pygame.font.SysFont(None, 30)

        self.main_box = pygame.Rect(x, y, width, height)
        self.inc_img = pygame.image.load(str(self.cd / 'images/arrow_basic_e_small.png')).convert_alpha()
        self.dec_img = pygame.image.load(str(self.cd / 'images/arrow_basic_w_small.png')).convert_alpha()
        self.inc_img_rect = self.inc_img.get_rect(topright=(self.main_box.topright[0], y + 3))
        self.dec_img_rect = self.dec_img.get_rect(topleft=(x, y + 3))

    def input_num(self) -> Tuple[pygame.Surface, pygame.Rect]:
        t = self.font.render(f"{self.var}", 1, self.black)
        t_rect = t.get_rect(center=self.main_box.center)
        return t, t_rect
    
    def draw(self, win: pygame.Surface) -> None:
        pygame.draw.rect(win, self.gray, self.main_box)
        win.blit(self.dec_img, self.dec_img_rect)
        win.blit(self.inc_img, self.inc_img_rect)
        win.blit(*self.input_num())

    def up(self, pos: Tuple[int, int]) -> bool:
        return self.inc_img_rect.collidepoint(pos)

    def down(self, pos: Tuple[int, int]) -> bool:
        return self.dec_img_rect.collidepoint(pos)
            