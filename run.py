from lib2d.game import Game
from lib2d.playerinput import KeyboardPlayerInput
from lib2d import gfx, context
import pygame
import logging

logging.basicConfig(level=100)

profile = 1


class TestGame(Game):
    def start(self):
        from lib.titlescreen import TitleScreen
        gfx.set_screen((1024, 600), 3, "scale")
        self.sd.inputs.append(KeyboardPlayerInput())
        self.sd.reload_screen()
        self.sd.append(TitleScreen())
        self.sd.run()

if __name__ == "__main__":
    if profile:
        import cProfile
        import pstats
        import sys

        game = TestGame()

        try:
            cProfile.run('game.start()', "results.prof")
        except KeyboardInterrupt:
            raise
        else:
            p = pstats.Stats("results.prof")
            p.strip_dirs()
            p.sort_stats('time').print_stats(20, "^((?!pygame).)*$")
            p.sort_stats('time').print_stats(20)

    else:
        TestGame().start()

    pygame.quit()
