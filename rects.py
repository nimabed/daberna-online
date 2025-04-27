import pygame
from typing import Tuple

class Rects:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, text_size: int) -> None:
        self.x: int = x
        self.y: int = y
        self.text: str = text
        self.width: int = width
        self.height: int = height
        self.font: pygame.font.Font = pygame.font.SysFont("Lato Black", text_size)

    def draw_player(self, win: pygame.Surface) -> None:
        pygame.draw.rect(win, (0,0,255), (self.x, self.y, self.width, self.height), 2)
        num = self.font.render(self.text, 1, (0,0,0))
        win.blit(num, (self.x + self.width/2 - num.get_width()/2, self.y + self.height/2 - num.get_height()/2))

    def draw_opponent(self, win: pygame.Surface) -> None:
        if self.text == "*":
            pygame.draw.rect(win, (0,0,255), (self.x, self.y, self.width, self.height))
        else:
            pygame.draw.rect(win, (0,0,255), (self.x, self.y, self.width, self.height), 2)
            num = self.font.render(self.text, 1, (0,0,0))
            win.blit(num, (self.x + self.width/2 - num.get_width()/2, self.y + self.height/2 - num.get_height()/2))
    
    def clicked(self, pos: Tuple[int, int]) -> bool:
        if (self.x <= pos[0] <= self.x + self.width) and (self.y <= pos[1]<= self.y + self.height):
            return True
        else:
            return False

    def draw_lines(self, win: pygame.Surface) -> None:
        pygame.draw.line(win, (255,0,0), (self.x+10, self.y+10), (self.x+self.width-10, self.y+self.height-10), 3)
        pygame.draw.line(win, (255,0,0), (self.x+self.width-10,self.y+10), (self.x+10, self.y+self.height-10), 3) 

    def fill_rect(self, win: pygame.Surface) -> None:
        pygame.draw.rect(win, (0,240,0), (self.x, self.y, self.width, self.height))