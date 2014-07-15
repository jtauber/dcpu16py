import pygame


class Terminal:

    COLORS = [
        (0, 0, 0),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255)
    ]

    def __init__(self, args):
        self.width = args.width
        self.height = args.height
        self.keys = []
        pygame.font.init()
        self.font = pygame.font.match_font("Monospace,dejavusansmono")
        self.font = pygame.font.get_default_font() if not self.font else self.font
        self.font = pygame.font.Font(self.font, 12)
        self.cell_width = max([self.font.metrics(chr(c))[0][1] for c in range(0, 128)])
        self.cell_height = self.font.get_height()
        win_width = self.cell_width * args.width
        win_height = self.cell_height * args.height
        self.screen = pygame.display.set_mode((win_width, win_height))

    def update_character(self, row, column, character, color=None):
        if not color or (not color[0] and not color[1]):
            fgcolor = self.COLORS[7]
            bgcolor = self.COLORS[0]
        else:
            fgcolor = self.COLORS[color[0]]
            bgcolor = self.COLORS[color[1]]
        surf = pygame.Surface((self.cell_width, self.cell_height))
        surf.fill(pygame.Color(*bgcolor))
        char = self.font.render(chr(character), True, fgcolor)
        surf.blit(char, (1, 1))
        self.screen.blit(surf, (column * self.cell_width, row * self.cell_height))

    def show(self):
        pass

    def updatekeys(self):
        events = pygame.event.get(pygame.KEYDOWN)
        for e in events:
            key = e.unicode
            if key:
                self.keys.insert(0, ord(e.unicode))

    def redraw(self):
        pygame.display.flip()

    def quit(self):
        pass
