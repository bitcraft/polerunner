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
from playerinput import KeyboardPlayerInput, MousePlayerInput
from collections import deque
from itertools import cycle, islice
from pygame.locals import *


"""
player's input doesn't get checked every loop.  it is checked every 15ms and
then handled.  this prevents the game logic from dealing with input too often
and slowing down rendering.
"""





class Context(object):
    """
    Game states are a logical way to break up distinct portions
    of a game.
    """

    def __init__(self, parent):
        """
        Called when object is instanced.

        parent is a ref to the statedriver

        Not a good idea to load large objects here since it is possible
        that the state is simply instanced and placed in a queue.

        Ideally, any initialization will be handled in activate() since
        that is the point when assets will be required.
        """        

        self.parent = parent
        self.activated = False


    def activate(self):
        """
        Called when focus is given to the state for the first time

        *** When overriding this method, set activated to true ***
        """

        pass


    def reactivate(self):
        """
        Called with focus is given to the state again
        """

        pass


    def deactivate(self):
        """
        Called when focus is being lost
        """

        pass


    def terminate(self):
        """
        Called when the state is no longer needed
        The state will be lost after this is called
        """

        pass


    def draw(self, surface):
        """
        Called when state can draw to the screen
        """

        pass


    def handle_event(self, event):
        """
        Called when there is an pygame event to process

        Better to use handle_command() or handle_commandlist()
        for player input
        """

        pass


    def handle_command(self, command):
        """
        Called when there is an input command to process
        """
 
        pass


    def handle_commandlist(self, cmdlist):
        """
        Called when there are multiple input commands to process
        This is more effecient that handling them one at a time
        """

        pass





def flush_cmds(cmds):
    pass


class StatePlaceholder(object):
    """
    holds a ref to a state

    when found in the queue, will be instanced
    """

    def __init__(self, klass):
        self.klass = klass

    def activate(self):
        pass

    def deactivate(self):
        pass


class ContextDriver(object):
    """
    A state driver controls what is displayed and where input goes.

    A state is a logical way to break up "modes" of use for a game.
    For example, a title screen, options screen, normal play, pause,
    etc.
    """

    def __init__(self, parent, inputs, target_fps=30):
        self.parent = parent
        self._stack = deque()
        self.target_fps = target_fps
        self.inputs = inputs

        self.inputs.append(KeyboardPlayerInput())
        #self.inputs.append(MousePlayerInput())

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


    def done(self):
        """
        deactivate the current state and activate the next state, if any
        """

        self.getCurrentState().deactivate()
        self._stack.pop()
        state = self.getCurrentState()

        if isinstance(state, StatePlaceholder):
            self.replace(state.klass())
           
        elif state is not None:
            if state.activated:
                state.reactivate()
            else:
                state.activate()

    def getCurrentState(self):
        try:
            return self._stack[-1]
        except:
            return None


    def replace(self, state):
        """
        start a new state and deactivate the current one
        """

        self.getCurrentState().deactivate()
        self._stack.pop()
        self.start(state)


    def start(self, state):
        """
        start a new state and hold the current state.

        when the new state finishes, the previous one will continue
        where it was left off.

        idea: the old state could be pickled and stored to disk.
        """

        self._stack.append(state)
        self.getCurrentState().activate()
        self.getCurrentState().activated = True


    def start_restart(self, state):
        """
        start a new state and hold the current state.

        the current state will be terminated and a placeholder will be
        placed on the stack.  when the new state finishes, the previous
        state will be re-instanced.  this can be used to conserve memory.
        """

        prev = self.getCurrentState()
        prev.deactivate()
        self._stack.pop()
        self._stack.append(StatePlaceholder(prev.__class__))
        self.start(state)


    def push(self, state):
        self._stack.appendleft(state)


    def roundrobin(*iterables):
        """
        create a new schedule for concurrent states
        roundrobin('ABC', 'D', 'EF') --> A D E B F C

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


    def run(self):
        """
        run the state driver.
        """

        # deref for speed
        event_poll = pygame.event.poll
        event_pump = pygame.event.pump
        current_state = self.getCurrentState
        clock = pygame.time.Clock()

        # streamline event processing by filtering out stuff we won't use
        allowed = [QUIT, KEYDOWN, KEYUP, \
                   MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION]

        pygame.event.set_allowed(None)
        pygame.event.set_allowed(allowed)

        # set an event to flush out commands
        event_flush = pygame.USEREVENT
        pygame.time.set_timer(event_flush, 20)

        # set an event to update the game state
        debug_output = pygame.USEREVENT + 1
        pygame.time.set_timer(debug_output, 2000)

        # make sure our custom events will be triggered
        pygame.event.set_allowed([event_flush, debug_output])

        # some stuff to handle the command queue
        rawcmds = 0
        cmdlist = []
        checkedcmds = []
        
        currentState = current_state()
        while currentState:
            time = clock.tick(self.target_fps)

            event = event_poll()
            while event:

                # check each input for something interesting
                for cmd in [ c.getCommand(event) for c in self.inputs ]:
                    rawcmds += 1
                    if (cmd != None) and (cmd[:2] not in checkedcmds):
                        checkedcmds.append(cmd[:2])
                        cmdlist.append(cmd)

                # we should quit
                if event.type == QUIT:
                    currentState = None
                    break

                # do we flush input now?
                elif event.type == event_flush:
                    currentState.handle_commandlist(cmdlist)
                    [ currentState.handle_commandlist(i.getHeld())
                    for i in self.inputs ]
                    rawcmds = 0
                    checkedcmds = []
                    cmdlist = []


                # do we flush input now?
                elif event.type == debug_output:
                    print "current FPS: \t{0:.1f}".format(clock.get_fps())

                # back out of this state, or send event to the state
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.done()
                        break
                    else:
                        currentState.handle_event(event)
                else:
                    currentState.handle_event(event)

                event = event_poll()

            originalState = current_state()
            if currentState: currentState = originalState

            if currentState:
                dirty = currentState.draw(self._screen)
                gfx.update_display(dirty)
                #gfx.update_display()

                # looks awkward?  because it is.  forcibly give small updates
                # to each object so we don't draw too often.

                time = time / 5.0
                #print time, self.target_fps / 10.0

                currentState.update(time)
                currentState = current_state()
                if not currentState == originalState: continue
                currentState.update(time)
                currentState = current_state()
                if not currentState == originalState: continue
                currentState.update(time)
                currentState = current_state()
                if not currentState == originalState: continue
                currentState.update(time)
                currentState = current_state()
                if not currentState == originalState: continue
                currentState.update(time)
                currentState = current_state()
