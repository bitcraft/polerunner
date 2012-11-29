#!/usr/bin/env python

from lib2d import res, gfx, context
import pygame
from pygame.locals import *


class Game(object):
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        gfx.init()
        self.sd = GameDriver(self, 60)

    def get_screen(self):
        return gfx.screen

    def start(self):
        pass


class GameContext(context.Context):
    def draw(self, surface):
        """
        Called when context can draw to the screen
        """
        pass


    def handle_command(self, command):
        """
        Called when there is an input command to process
        """
        pass


    def update(self, time):
        pass


class GameDriver(context.ContextDriver):
    """
    accepts contexts that control game flow
    A context is a logical way to break up "modes" of use for a game.
    For example, a title screen, options screen, normal play, pause, etc.
    """

    def __init__(self, parent, target_fps=30):
        context.ContextDriver.__init__(self)
        self.parent = parent
        self.target_fps = target_fps
        self.inputs = []

        tpf = 1.0 / self.target_fps
        self.update_steps = 3.0
        self.time_delta = tpf / float(self.update_steps)

        if parent != None:
            self.reload_screen()


    def get_size(self):
        """
        Return the size of the surface that is being drawn on.

        * This may differ from the size of the window or screen if the display
        is set to scale.
        """

        return self.parent.get_screen().get_size()


    def get_screen(self):
        """
        Return the surface that is being drawn to.

        * This may not be the pygame display surface
        """

        return self.parent.get_screen()


    def reload_screen(self):
        """
        Called when the display changes mode.
        """

        self._screen = self.parent.get_screen()


    def run(self):
        """
        run the context driver.  this is effectively your 'main loop' and game.
        """

        # deref for speed
        event_poll = pygame.event.poll
        event_pump = pygame.event.pump
        clock = pygame.time.Clock()

        # streamline event processing by filtering out stuff we won't use
        allowed = [QUIT, KEYDOWN, KEYUP, \
                   MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION]

        pygame.event.set_allowed(None)
        pygame.event.set_allowed(allowed)

        # set an event to update the game context
        debug_output = pygame.USEREVENT
        pygame.time.set_timer(debug_output, 2000)

        # make sure our custom events will be triggered
        pygame.event.set_allowed([debug_output])

        this_context = self.current_context

        # this will loop until the end of the program
        while self.current_context and this_context:
            this_context = self.current_context
            time = clock.tick(self.target_fps)

# =============================================================================
# EVENT HANDLING ==============================================================

            event = event_poll()
            while event:

                # we should quit
                if event.type == QUIT:
                    this_context = None
                    break

                # check each input for something interesting
                for cmd in [ c.getCommand(event) for c in self.inputs ]:
                    if cmd is not None:
                        this_context.handle_command(cmd)
                        if not self.current_context == this_context:
                            break

                if not self.current_context == this_context: break

                if event.type == debug_output:
                    print "current FPS: \t{0:.1f}".format(clock.get_fps())
                    print "context stack", self._stack
                    print "current context", self.current_context

                # back out of this context, or send event to the context
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.remove(self.current_context)
                        break

                event = event_poll()

# =============================================================================
# STATE UPDATING AND DRAWING HANDLING =========================================

            if self.current_context is this_context:
                dirty = this_context.draw(self._screen)
                gfx.update_display(dirty)
                #gfx.update_display()

                # looks awkward?  because it is.  forcibly give small updates
                # to the context so we don't draw too often.

                this_context.update(self.time_delta)
                if not self.current_context == this_context: continue

                this_context.update(self.time_delta)
                if not self.current_context == this_context: continue

                this_context.update(self.time_delta)
                current_context = self.current_context

