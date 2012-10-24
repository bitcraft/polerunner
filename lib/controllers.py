"""
command tree for the main character
"""

from lib2d.buttons import *
from lib2d.fsa import STICKY
import lib2d
import pygame


INITIAL_WALK_SPEED = 10
RUN_SPEED = 50
SPRINT_SPEED = 110
WALK_SPEED_INCREMENT = .5
ROLLING_FRICTION = 0.99


class state(object):
    flags = 0
    forbidden = []

    def __init__(self, fsa, entity, *args, **kwargs):
        self.fsa = fsa
        self.entity = entity

    def abort(self):
        self.fsa.process((self, STATE_VIRTUAL, ANIMATION_FINISHED))

    def enter(self, cmd=None):
        pass

    def exit(self, cmd=None):
        pass

    def update(self, time):
        pass


class walkState(state):
    flags = STICKY

    def enter(self, cmd):
        self.body = self.entity.parent.getBody(self.entity)
        self.cmd = cmd
        if self.cmd[0] == P1_LEFT:
            self.entity.avatar.flip = 1
            self.x = -INITIAL_WALK_SPEED
        elif self.cmd[0] == P1_RIGHT:
            self.entity.avatar.flip = 0
            self.x = INITIAL_WALK_SPEED


    def update(self, tine):
        self.body.velocity.x = self.x

        if self.x > 0:
            self.x += WALK_SPEED_INCREMENT
        else:
            self.x -= WALK_SPEED_INCREMENT

        vel = abs(self.body.velocity.x)
        if vel < RUN_SPEED:
            self.entity.avatar.play('walk')
        elif vel >= RUN_SPEED and vel < SPRINT_SPEED:
            self.entity.avatar.play('run')
        elif vel >= SPRINT_SPEED:
            self.entity.avatar.play('sprint')


class crouchState(state):
    forbidden = [walkState]

    def enter(self, cmd):
        self.entity.avatar.play('crouch', loop_frame=4)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = 0

class uncrouchState(state):
    def enter(self, cmd):
        self.entity.avatar.play('uncrouch', callback=self.abort ,loop=0)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = 0

class jumpState(state):
    def enter(self, cmd):
        area = self.entity.parent
        self.body = self.entity.parent.getBody(self.entity)

        if self.entity.grounded:
            self.entity.jumps = 1
            if not self.entity.held:
                self.body.apply_impulse((0, -self.entity.jump_strength))
        else:
            # double jump
            if self.entity.jumps <= 10:
                self.entity.jumps += 2
                self.body.apply_impulse((0, -self.entity.jump_strength))

    def update(self, time):
        if self.body.velocity.y > 0:
            self.abort()

class fallRecoverState(state):
    forbidden = [walkState]

    def enter(self, cmd):
        self.entity.avatar.play('crouch', callback=self.abort ,loop=0)


class deadState(state):
    def enter(self, cmd):
        self.entity.avatar.play('die', loop_frame=2)

class upState(state):
    pass

class runState(state):
    pass

class sprintState(state):
    pass

class idleState(state):
    forbidden = [walkState]

    def enter(self, cmd):
        self.entity.avatar.play('idle')
        body = self.entity.parent.getBody(self.entity)
        if body.velocity.y == 0.0:
            self.fsa.eject(walkState)
            body.velocity.x = 0
            self.entity.jumps = 0

    def update(self, time):
        body = self.entity.parent.getBody(self.entity)
        if body.velocity.y > 0:
            self.abort()

class brakeState(state):
    forbidden = [walkState]

    def enter(self, cmd):
        self.entity.avatar.play('brake', callback=self.abort ,loop=0)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = body.velocity.x / 10.0

class fallingState(state):
    def enter(self, cmd):
        self.entity.avatar.play('falling')
        self.body = self.entity.parent.getBody(self.entity)
        self.old_vel = self.body.velocity.y 
 
    def update(self, time):
        if self.old_vel > 0:
            if round(self.body.velocity.y, 4) == 0:
                if self.old_vel > 2:
                    #self.fsa.change_state(die)
                    self.fsa.change_state(fallRecover)
                else:
                    self.fsa.change_state(fallRecover)
        self.old_vel = self.body.velocity.y 

class rollingState(state):
    forbidden = [walkState]

    def enter(self, cmd):
        self.original = self.entity.avatar.animations['roll'].image
        self.entity.avatar.play('roll')
        self.angle = 0.0

    def update(self, time):
        self.angle -= 2.0
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x *= ROLLING_FRICTION
        colorkey = self.original.get_at((0,0))
        rotated = pygame.transform.rotate(self.original, self.angle)
        self.entity.avatar.animations['roll'].image = rotated
        if abs(body.velocity.x) < INITIAL_WALK_SPEED:
            self.entity.avatar.animations['roll'].image = self.original
            self.abort()


# =============================================================================
# state function pickers

class transition(object):
    def pick(self, fsa, entity):
        pass

class dieT(transition):
    def pick(self, fsa, entity):
        return deadState(fsa, entity)
die = dieT().pick

class idleT(transition):
    def pick(self, fsa, entity):
        body = entity.parent.getBody(entity)
        if body.velocity.y > 0:
            return fallingState(fsa, entity)

        if abs(body.velocity.x) > 1.3:
            return brakeState(fsa, entity)
        else:
            return idleState(fsa, entity)
idle = idleT().pick

class moveT(transition):
    def pick(self, fsa, entity):
        return walkState(fsa, entity)
move = moveT().pick

class crouchT(transition):
    def pick(self, fsa, entity):
        body = entity.parent.getBody(entity)
        if abs(body.velocity.x) > 1.2:
            return rollingState(fsa, entity)
        else:
            return crouchState(fsa, entity)
crouch = crouchT().pick

class uncrouchT(transition):
    def pick(self, fsa, entity):
        return uncrouchState(fsa, entity)
uncrouch = uncrouchT().pick

class upT(transition):
    def pick(self, fsa, entity):
        return jumpState(fsa, entity)
up = upT().pick

class fallRecoverT(transition):
    def pick(self, fsa, entity):
        body = entity.parent.getBody(entity)
        if abs(body.velocity.x) >= 1.2:
            return rollingState(fsa, entity)
        elif 1.2 > abs(body.velocity.x):
            return fallRecoverState(fsa, entity)
fallRecover = fallRecoverT().pick

class jumpT(transition):
    def pick(self, fsa, entity):
        return jumpState(fsa, entity)
jump = jumpT().pick

def stickyTrigger(trigger, state, picker):
    return (trigger, BUTTONDOWN), state, picker, (trigger, BUTTONUP)

#
# =============================================================================

class HeroController(lib2d.fsa):

    def setup(self):

        # environmental triggers
        self.at((FALL_DAMAGE, None), fallingState, fallRecover)
        self.at((STATE_VIRTUAL, ANIMATION_FINISHED), fallRecoverState,uncrouch)


        # position and movement
        self.at(*stickyTrigger(P1_LEFT, idleState, move))
        self.at(*stickyTrigger(P1_RIGHT, idleState, move))
        self.at((P1_LEFT, BUTTONDOWN), walkState, move)
        self.at((P1_RIGHT, BUTTONDOWN), walkState, move)

        self.at((P1_LEFT, BUTTONDOWN), brakeState, move)
        self.at((P1_RIGHT, BUTTONDOWN), brakeState, move)

        self.at((P1_LEFT, BUTTONDOWN), uncrouchState, move)
        self.at((P1_RIGHT, BUTTONDOWN), uncrouchState, move)

        self.at((STATE_VIRTUAL, ANIMATION_FINISHED), uncrouchState, idle)
        self.at((STATE_VIRTUAL, ANIMATION_FINISHED), brakeState, idle)

        self.at((P1_LEFT, BUTTONUP), walkState, idle)
        self.at((P1_RIGHT, BUTTONUP), walkState, idle)


        # self.crouch / elevator control
        self.at((P1_DOWN, BUTTONDOWN), idleState, crouch)
        self.at((P1_DOWN, BUTTONDOWN), walkState, crouch)
        self.at((P1_DOWN, BUTTONDOWN), runState, crouch)
        self.at((P1_DOWN, BUTTONDOWN), sprintState, crouch)

        self.at((P1_DOWN, BUTTONUP), crouchState, uncrouch)
        self.at((STATE_VIRTUAL, ANIMATION_FINISHED), rollingState, uncrouch)


        # elevator control 
        #self.at((P1_UP, BUTTONDOWN), idleState, up)
        #self.at((P1_UP, BUTTONUP), upState, idle)


        # self.jumping
        self.at((P1_ACTION2, BUTTONDOWN), idleState, jump)
        self.at((P1_ACTION2, BUTTONDOWN), walkState, jump)
        self.at((P1_ACTION2, BUTTONDOWN), runState, jump)
        self.at((P1_ACTION2, BUTTONDOWN), sprintState, jump)

        self.at((P1_ACTION2, BUTTONUP), jumpState, idle)

        self.at((STATE_VIRTUAL, ANIMATION_FINISHED), fallingState, idle)


        # meh
        self.at((STATE_VIRTUAL, ANIMATION_FINISHED), idleState, idle)

        #self.change_state((idle, None), None)
        self.change_state(idle, None)

