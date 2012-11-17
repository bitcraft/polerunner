"""
Copyright 2010, 2011  Leif Theden


This file is part of lib2d.

lib2d is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

lib2d is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with lib2d.  If not, see <http://www.gnu.org/licenses/>.
"""

import gfx
import pygame
from lib2d.objects import GameObject
from collections import deque
from itertools import cycle, islice
from pygame.locals import *


class Context(object):
    """
    Contexts are used anywhere a handler uses a stack to manage information.
    Currently are used in:
        Context Driver for the game
        FSA for controller handling
    """

    def __init__(self, driver=None):
        """
        Called when object is instanced.

        Please do not extend this method

        Ideally, any initialization will be handled in init() since that is the
        point when assets will be required.
        """        

        self.driver = driver


    def init(self, *args, **kwargs):
        """
        Called after context is placed in a stack
        This will only be called once over the lifetime of a context
        """

        pass


    def enter(self):
        """
        Called before focus is given to the context
        This may be called several times over the lifetime of the context
        """

        pass


    def exit(self):
        """
        Called before focus is lost
        This may be called several times over the lifetime of the context
        """

        pass


    def terminate(self):
        """
        Called before the context is removed from a stack
        This will only be called once
        """

        pass


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


class ContextDriver(object):

    def __init__(self):
        self._stack = []


    def remove(self, context, terminate=True):

        print "REMOVE", context, self._stack

        # you can optionally ignore the contexts terminate method
        # this behavior is could easily break your stack, so use sparingly
        if terminate:
            context.terminate()

        # this may be the current context, so handle it differently
        if context is self.current_context:
            context.exit()
            try:
                self._stack.remove(context)
            except:
                raise Exception, context
            current_context = self.current_context
            if current_context:
                current_context.enter()
        else:
            context.exit()
            try:
                self._stack.remove(context)
            except:
                raise Exception, context


    def queue(self, new_context, *args, **kwargs):
        """
        queue a context just before the current context
        when the current context finishes, the context passed will be run
        """

        self._stack.insert(-1, new_context)
        new_context.driver = self
        new_context.init(*args, **kwargs)


    def append(self, new_context, *args, **kwargs):
        """
        start a new context and hold the current context.

        when the new context finishes, the previous one will continue
        where it was left off.

        idea: the old context could be pickled and stored to disk.
        """

        current_context = self.current_context
        if current_context:
            current_context.exit()

        self._stack.append(new_context)
        new_context.driver = self
        new_context.init(*args, **kwargs)
        new_context.enter()


    def roundrobin(*iterables):
        """
        create a new schedule for concurrent contexts
        roundrobin('ABC', 'D', 'EF') --> A D E B F C

        NOT USED

        Recipe credited to George Sakkis
        """

        pending = len(iterables)
        nexts = cycle(iter(it).next for it in iterables)
        while pending:
            try:
                for next in nexts:
                    yield next()
            except StopIteration:
                pending -= 1
                nexts = cycle(islice(nexts, pending))


    @property
    def current_context(self):
        try:
            return self._stack[-1]
        except IndexError:
            return None


class GameDriver(ContextDriver):
    """
    accepts contexts that control game flow
    A context is a logical way to break up "modes" of use for a game.
    For example, a title screen, options screen, normal play, pause,
    etc.
    """

    def __init__(self, parent, target_fps=30):
        ContextDriver.__init__(self)
        self.parent = parent
        self.target_fps = target_fps
        self.inputs = []

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

                time = time / 5.0

                this_context.update(time)
                if not self.current_context == this_context: continue

                this_context.update(time)
                if not self.current_context == this_context: continue

                this_context.update(time)
                if not self.current_context == this_context: continue

                this_context.update(time)
                if not self.current_context == this_context: continue

                this_context.update(time)
                current_context = self.current_context

