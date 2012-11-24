from lib.levelstate import LevelState
from lib import world

from lib2d.ui import Menu
from lib2d.image import Image
from lib2d.objects import loadObject
from lib2d import res, draw, game

import pygame, os


class InstructionScreen(game.GameContext):
    def enter(self):
        self.foreground = (0,0,0)
        self.background = (109, 109, 109)
        self.border = draw.GraphicBox("border0.png", hollow=True)
        self.msgFont = pygame.font.Font((res.fontPath("volter.ttf")), 9)
        self.activated = True
        self.redraw = True


    def draw(self, surface):
        if self.redraw:
            sw, sh = surface.get_size()
            self.redraw = False
            self.borderFilled.draw(surface, surface.get_rect().inflate(6,6))
            rect = pygame.Rect((sw*.05, sh*.05, sw*.90, sh*.90))
            draw.drawText(surface, hints, (128, 129, 129),
                          rect.move(1,1), self.msgFont)
            draw.drawText(surface, hints, self.foreground, rect, self.msgFont)


    def handle_event(self, event):
        if event.type == pygame.locals.KEYDOWN:
            self.driver.done()


class TitleScreen(game.GameContext):
    borderImage = Image("lpc-border0.png", colorkey=True)

    def init(self):
        self.background = (109, 109, 109)
        self.border = draw.GraphicBox(self.borderImage)
        self.counter = 0
        self.game = None


    def enter(self):
        self.redraw = True

        # temporary hack so that game bypasses the title screen menu
        if self.game is None:
            self.new_game()
            return


        if self.game:
            self.menu = Menu(20, -5, 'vertical', 100,
                [('New Game', self.new_game),
                ('Continue', self.continue_game),
                #('Save', self.save_game),
                #('Reload', self.load_game),
                #('Save and Quit', self.savequit_game),
                ('Quit', self.quit_game)],
                font="visitor1.ttf", font_size=20)
        else:
            self.menu = Menu(20, -5, 'vertical', 100,
                [('New Game', self.new_game),
                #('Continue', self.load_game),
                ('Introduction', self.show_intro),
                ('Quit', self.quit_game)],
                font="visitor1.ttf", font_size=20)

        self.menu.rect = pygame.Rect(12,12,20,100)


    def handle_command(self, cmd):
        self.menu.handle_command(cmd)


    def draw(self, surface):
        if self.redraw:
            self.redraw = False
            #if self.game:
            self.border.draw(surface, surface.get_rect(), fill=200)

        self.menu.draw(surface)


    def new_game(self):
        if self.game:
            self.game.unload()
            self.game = None

        res.fadeoutMusic(1000)
        self.game = world.build()
        level = self.game.getChildByGUID(5001)
        self.driver.append(LevelState(level))


    def save_game(self):
        path = os.path.join("resources", "saves", "save")
        [ i.unload() for i in self.game.getChildren() ]
        self.game.save(path)
        self.continue_game()


    def load_game(self):
        if self.game:
            self.game.unload()
            self.game = None

        try:
            path = os.path.join("resources", "saves", "save")
            self.game = loadObject(path)
        except IOError:
            return self.new_game()

        level = self.game.getChildByGUID(5001)
        self.driver.append(LevelState(level))


    def continue_game(self):
        res.fadeoutMusic(1000)
        level = self.game.getChildByGUID(5001)
        self.driver.append(LevelState(level))


    def show_intro(self):
        self.driver.start_restart(InstructionScreen())


    def savequit_game(self):
        if self.game:
            path = os.path.join("resources", "saves", "save")
            [ i.unload() for i in self.game.getChildren() ]
            self.game.save(path)
        self.quit_game()


    def quit_game(self):
        self.driver.remove(self) 

