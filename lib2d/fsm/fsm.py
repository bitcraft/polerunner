"""
Copyright 2009, 2010, 2011 Leif Theden

This file is part of lib2d.

lib2d is free software: you can redistribute it
and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

lib2d is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with lib2d.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
modified state machine.  controls player input

uses the term 'context' in place of 'state' for consistancy with lib2d
"""

from lib2d import context
from lib2d.buttons import *
from flags import *
from collections import namedtuple


DEBUG = 0

def debug(message):
    if DEBUG: print message


Trigger = namedtuple('Trigger', 'owner, cmd, arg')
Condition = namedtuple('Condition', 'trigger, context')
Transition = namedtuple('Transition', 'func, alt_trigger, flags')


class State(context.Context):
    """
    States are used with the 'fsm' to handle player input
    """

    # allows the state to clean up and sends 'state finished' event to the fsm
    def __exit__(self):
        self.exit()
        self.parent.process((self.__class__, STATE_VIRTUAL, STATE_FINISHED))

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    # allows the state to end cleanly
    def stop(self):
        try:
            self.parent.remove(self)
        except ValueError:
            print "FAILED TO REMOVE {}".format(self)

    # stops the state without calling the exit() method
    # also prevents the the end state trigger from being processed
    def abort(self):
        try:
            self.parent.remove(self, exit=False)
        except ValueError:
            print "FAILED TO REMOVE {}".format(self)

    def collide(self, *args, **kwargs):
        self.parent.process((self.__class__, STATE_VIRTUAL, COLLISION))

    def update(self, time):
        pass


class InputFSM(context.ContextDriver):
    """
    Finate state machine that is designed to work with player input

    Acceptes states and transistions and has some built-in functions that
    gracefully handle player input.
    """

    def __init__(self, entity):
        context.ContextDriver.__init__(self)

        self.entity = entity

        self.transitions = {}
        self.transitions_wildcard = {}
        self.combos = {}
        self.button_combos = []
        self.move_history = []
        self.button_history = []
        self.holds = {}         # keep track of context changes from holds
        self.time = 0
        self._queue = []
        self._inProcess = False

    def setup(self):
        pass

    def add_transition(self, trigger, ctx, func, alt_trigger=None, flags=0):
        """
        add new "transition".
        """

        cond = Condition(trigger, ctx)
        trans = Transition(func, alt_trigger, flags)

        if ctx == None:
            self.transitions_wildcard[cond] = trans
        else:
            self.transitions[cond] = trans

    # shorthand for adding transitions
    at = add_transition

    def add_button_combo(self, animation, timeout, *buttons):
        """
        add a new button combo.

        button combos are executed when a series of buttons are pressed quickly.
        timeout specifies a limit on the time allowed between each button press
        """
        pass

    def add_combo(self, animation, *combo):
        """
        add a new animation combo.

        a combo is a list of animations.  if it matches the command history,
        then execute another animation.

        command history is cleared each time the fighter idles, so it is safe
        to assume that the command sequence starts from an idle
        """
        pass

    def get_transition(self, trigger, ctx=None):
        if ctx == None:
            ctx = self.current_context.__class__

        try:
            return self.transitions_wildcard[(trigger, None)]
        except KeyError:
            return self.transitions.get((trigger, ctx), None)

    def process(self, trigger, ctx=None):
        """
        Triggers are passed here.
        """

        if self._inProcess:
            self._queue.append(trigger)
            return
        else:
            self._inProcess = True

        debug("=========== current: {}".format(self.current_context))
        debug("=========== processing {}".format(trigger))
        debug("   {}".format(self._stack))
        transition = self.get_transition(trigger, ctx)

        self.remove_holds(trigger)

        debug("=========== found transition: {}".format(transition))

        if transition is None:
            self._inProcess = False
            self._emptyQueue()
            return

        new_context = transition.func(self, self.entity)

        if new_context is None:
            self._inProcess = False
            self._emptyQueue()
            return

        trigger = Trigger(*trigger)
        new_context.trigger = trigger

        # BREAK flag cancels the current context
        # can be used for move 'cancels'
        if transition.flags & BREAK == BREAK:
            old_context = self.current_context
            old_context.abort()
            self.append(new_context)

        elif transition.flags & SKIPEXIT == SKIPEXIT:
            pass

        # STUBBORN will add the context to the stack even if it already exists.
        # currently, this flag does nothing
        elif transition.flags & STUBBORN == STUBBORN:
            self.append(new_context)

        # QUEUED flag will cause context to be queued after current context
        elif transition.flags & QUEUED == QUEUED:
            self.queue(new_context)

        # no flags were found, so just add the new context normally
        else:
            self.append(new_context)

        # support 'toggled' (STICKY) transitions
        # transitions can specify a trigger in add_transition that
        # will remove them from the stack.  it is checked here.
        if transition.alt_trigger is not None:
            self.holds[transition.alt_trigger] = (new_context, transition, trigger)

        self._inProcess = False
        self._emptyQueue()

    def _emptyQueue(self):
        while self._queue:
            self.process(self._queue.pop())

    def remove_holds(self, trigger):
        try:
            ctx = self.holds[trigger][0]
        except:
            pass
        else:
            del self.holds[trigger]
            try:
                self.remove(ctx)
            except:
                debug("FSA: error {} not in holds".format(ctx))

    def update(self, time):
        self.time += time
        ctx = self.current_context
        if ctx:
            ctx.update(time) 
