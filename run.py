from lib2d.game import Game
from lib2d import gfx, context
import pygame



profile = 1


class TestGame(Game):
    def start(self):
        from lib.titlescreen import TitleScreen
        gfx.set_screen((1024, 600), 3, "scale")
        self.sd = context.ContextDriver(self, 60)
        self.sd.reload_screen()
        self.sd.start(TitleScreen(self.sd))
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
            pass
        else:
            p = pstats.Stats("results.prof")
            p.strip_dirs()
            p.sort_stats('time').print_stats(20, "^((?!pygame).)*$")
            p.sort_stats('time').print_stats(20)

    else:
        TestGame().start()

    pygame.quit()
