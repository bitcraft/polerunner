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


DEBUG = 1

def debug(message):
    if DEBUG: print message


Trigger = namedtuple('Trigger', 'owner, cmd, arg')
Condition = namedtuple('Condition', 'trigger, context')
Transition = namedtuple('Transition', 'func, alt_trigger, flags')

"""
class Transition(object):
    def build(self):
        pass


class Toggled(Transition):
    def __init__(self, trigger0, context, picker):
        self.args = (trigger0, context, picker)

    def build(self):
        pass
"""


class fsa(context.ContextDriver):
    """
    Somewhat like a finite context machine.
    """

    def __init__(self, entity):
        context.ContextDriver.__init__(self)

        self.entity = entity

        self.context_transitions = {}
        self.combos = {}
        self.button_combos = []
        self.move_history = []
        self.button_history = []
        self.holds = {}         # keep track of context changes from holds
        self.hold = 0           # keep track of buttons held down
        self.time = 0


    def setup(self):
        pass


    def add_transition(self, trigger, context, func, alt_trigger=None, flags=0):
        """
        add new "transition".
        """

        c = Condition(trigger, context)
        t = Transition(func, alt_trigger, flags)

        self.context_transitions[c] = t

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


    def get_transition(self, trigger, context=None):
        if context == None:
            context = self.current_context.__class__

        try:
            return self.context_transitions[(trigger, context)]
        except KeyError:
            return None


    def process(self, trigger):
        """
        Triggers are passed here.
        """


        transition = self.get_transition(trigger)

        debug("=========== processing {} {}".format(trigger, transition))

        self.remove_holds(trigger)

        if transition is None:
            return

        new_context = transition.func(self, self.entity)

        if new_context is None:
            return

        # allow for context 'self canceling':
        # context can be replaced with new instance of same class
        #existing = [stack for stack in self.all_stacks
        #            if new_context.__class__ in [i.__class__ for i in stack]]


        # BREAK flag cancels the current context and ignores of transitions
        if transition.flags & BREAK == BREAK:
            self.remove(self.current_context, terminate=False)

        # STUBBORN will add the context to the stack even if it already
        # exists.
        elif transition.flags & STUBBORN == STUBBORN:
            self.current_context.enter(trigger)

        # QUEUED flag will cause context to be run after current one is
        # finished
        elif transition.flags & QUEUED == QUEUED:
            self.queue(new_context, cmd=trigger)

        # support 'toggled' (STICKY) transitions
        # transitions can specify a trigger in add_transition that
        # will remove them from the stack.  it is checked here.
        if transition.alt_trigger is not None:
            self.holds[transition.alt_trigger] = (new_context, transition, trigger)

        self.append(new_context, cmd=trigger)


    def remove_holds(self, trigger):
        try:
            context = self.holds[trigger][0]
        except:
            pass
        else:
            try:
                del self.holds[trigger]
                self.remove(context)
            except:
                print "FSA:", "error {} not in holds".format(context)
            


    def update(self, time):
        self.time += time
        context = self.current_context

        if context:
            context.update(time) 

