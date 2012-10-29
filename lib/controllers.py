"""
command tree for the main character
"""

from lib2d.buttons import *
from lib2d.fsa.flags import *
import lib2d
import pygame
import pymunk


INITIAL_WALK_SPEED = 10
RUN_SPEED = 50
SPRINT_SPEED = 110
WALK_SPEED_INCREMENT = .5
STOPPING_FRICTION = 0.991
ROLLING_FRICTION = 0.99


class state(object):
    flags = 0
    forbidden = []

    def __init__(self, fsa, entity, *args, **kwargs):
        self.fsa = fsa
        self.entity = entity
        self.cmd = None
        self.init()

    def init(self):
        pass

    def abort(self):
        self.fsa.eject(self)

    def terminate(self, cmd):
        self.fsa.process((self.__class__, STATE_VIRTUAL, STATE_FINISHED))

    def enter(self, cmd=None):
        pass

    def exit(self, cmd=None):
        pass

    def update(self, time):
        pass


class walkState(state):
    flags = STICKY + REPLACE_OWN_CLASS

    def enter(self, cmd):
        self.body = self.entity.parent.getBody(self.entity)
        if self.cmd is None:
            self.cmd = cmd[1:]

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
    def enter(self, cmd):
        self.entity.avatar.play('crouch', loop_frame=4)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = 0
        space = self.entity.parent.space
        for shape in space.shapes:
            if shape.body is body:
                break
        space.remove(shape)
        w, h = self.entity.size
        shape = pymunk.Poly.create_box(body, size=(w, h/2))
        self.entity.parent.shapes[self.entity] = shape
        body.position.y += 8
        space.add(shape)

class uncrouchState(state):
    def enter(self, cmd):
        self.entity.avatar.play('uncrouch', callback=self.abort, loop=0)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = 0
        space = self.entity.parent.space
        for shape in space.shapes:
            if shape.body is body:
                break
        space.remove(shape)
        w, h = self.entity.size
        shape = pymunk.Poly.create_box(body, size=(w, h))
        self.entity.parent.shapes[self.entity] = shape
        space.add(shape)

class jumpState(state):
    def enter(self, cmd):
        pass


class jumpingState(state):
    max_jumps = 2

    def init(self):
        self.jumps = 0

    def enter(self, cmd):
        if cmd is None:
            return 

        area = self.entity.parent
        self.body = self.entity.parent.getBody(self.entity)

        if abs(self.body.velocity.x) > RUN_SPEED:
            self.entity.avatar.play('jumping')

        if self.entity.grounded:
            self.jumps = 1
            if not self.entity.held:
                self.body.apply_impulse((0, -self.entity.jump_strength))
        else:
            if self.jumps <= self.max_jumps:
                self.jumps += 2
                self.body.apply_impulse((0, -self.entity.jump_strength))


    def update(self, time):
        if self.body.velocity.y > 0:
            self.abort()


class fallRecoverState(state):
    def enter(self, cmd):
        self.entity.avatar.play('crouch', loop_frame=4)
        self.body = self.entity.parent.getBody(self.entity)
        self.body.velocity.x /= 3.0

    def update(self, time):
        self.body.velocity.x *= STOPPING_FRICTION
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED/4.0:
            self.abort()


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
    def enter(self, cmd):
        self.entity.avatar.play('idle')
        self.body = self.entity.parent.getBody(self.entity)

    def update(self, time):
        pass
        #if body.velocity.y > 0:
        #    self.abort()


class brakeState(state):
    def enter(self, cmd):
        self.entity.avatar.play('brake', loop_frame=5)
        self.body = self.entity.parent.getBody(self.entity)
        self.body.velocity.x /= 5.0
        self.entity.parent.emitSound('stop.wav', entity=self.entity)

    def update(self, time):
        self.body.velocity.x *= STOPPING_FRICTION
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED/4.0:
            self.abort()


class unbrakeState(state):
    def enter(self, cmd):
        self.entity.avatar.play('unbrake', callback=self.abort, loop=0)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = 0


class fallingState(state):
    def enter(self, cmd):
        self.entity.avatar.play('falling')
        self.body = self.entity.parent.getBody(self.entity)
        self.old_vel = self.body.velocity.y 
 
    def update(self, time):
        if self.old_vel > 0:
            if round(self.body.velocity.y, 4) == 0:
                self.abort()
        else:
            self.abort()

        self.old_vel = self.body.velocity.y 


class rollingState(state):
    def init(self):
        self.original = self.entity.avatar.animations['roll'].image

    def enter(self, cmd):
        self.entity.avatar.play('roll')
        self.angle = 0.0
        body = self.entity.parent.getBody(self.entity)
        space = self.entity.parent.space
        for shape in space.shapes:
            if shape.body is body:
                break
        space.remove(shape)
        w, h = self.entity.size
        shape = pymunk.Poly.create_box(body, size=(w, h/3))
        self.entity.parent.shapes[self.entity] = shape
        space.add(shape)
        body.position.y += 8

    def update(self, time):
        self.angle -= 1.5
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
    def __call__(self, *arg, **kwarg):
        return self.pick(*arg, **kwarg)

    def pick(self, fsa, entity):
        pass

class dieT(transition):
    def pick(self, fsa, entity):
        return deadState(fsa, entity)


class checkFallingT(transition):
    def pick(self, fsa, entity):
        if entity.grounded:
            return fallRecoverState(fsa, entity)

        body = entity.parent.getBody(entity)

        # best guess that we are grounded
        if round(body.velocity.y, 1) == 0:
            return fallRecover(fsa, entity)

        elif body.velocity.y > 0:
            return fallingState(fsa, entity)

        elif body.velocity.y < 0:
            return fallingState(fsa, entity)

        else:
            return fallRecoverT(fsa, entity)


class idleT(transition):
    def pick(self, fsa, entity):
        return idleState(fsa, entity)


class brakeT(transition):
    def pick(self, fsa, entity):
        body = entity.parent.getBody(entity)
        vel_x = abs(body.velocity.x)

        if 0 < vel_x < SPRINT_SPEED:
            body.velocity.x = 0.0
            return None
        elif vel_x >= SPRINT_SPEED:
            return brakeState(fsa, entity)


class moveT(transition):
    def pick(self, fsa, entity):
        return walkState(fsa, entity)

class crouchT(transition):
    def pick(self, fsa, entity):
        body = entity.parent.getBody(entity)
        if abs(body.velocity.x) > 1.2:
            return rollingState(fsa, entity)
        else:
            return crouchState(fsa, entity)

class uncrouchT(transition):
    def pick(self, fsa, entity):
        return uncrouchState(fsa, entity)

class upT(transition):
    def pick(self, fsa, entity):
        return jumpingState(fsa, entity)

class fallRecoverT(transition):
    def pick(self, fsa, entity):
        body = entity.parent.getBody(entity)
        print body.velocity.x
        if abs(body.velocity.x) >= SPRINT_SPEED:
            return rollingState(fsa, entity)
        else:
            return fallRecoverState(fsa, entity)

class jumpT(transition):
    def pick(self, fsa, entity):
        return jumpingState(fsa, entity)


# STICKY means that state will be readded to the fsa stack when possible if it
# is ejected AND the the alternate trigger has not happened yet.
def stickyTrigger(source, trigger, state, picker):
    return (source, trigger, BUTTONDOWN), state, picker, (source, trigger, BUTTONUP)

def stickyHeldTrigger(source, trigger, state, picker):
    return (source, trigger, BUTTONHELD), state, picker, (trigger, BUTTONUP)

def endState(state, new_state):
    return (state, STATE_VIRTUAL, STATE_FINISHED), state, new_state

die = dieT()
idle = idleT()
brake = brakeT()
move = moveT()
crouch = crouchT()
uncrouch = uncrouchT()
up = upT()
fallRecover = fallRecoverT()
jump = jumpT()
checkFalling = checkFallingT()

#
# =============================================================================

class HeroController(lib2d.fsa.fsa):

    def setup(self, source):

        # position and movement
        self.at(*stickyTrigger(source, P1_LEFT, idleState, move))
        self.at(*stickyTrigger(source, P1_RIGHT, idleState, move))

        #self.at(*stickyTrigger(P1_LEFT, walkState, brake))
        #self.at(*stickyTrigger(P1_RIGHT, walkState, brake))

        self.at(*endState(walkState, brake))

        self.at(*stickyTrigger(source, P1_LEFT, unbrakeState, move), flags=QUEUED)
        self.at(*stickyTrigger(source, P1_RIGHT, unbrakeState, move), flags=QUEUED)
        self.at(*stickyTrigger(source, P1_LEFT, brakeState, move), flags=QUEUED)
        self.at(*stickyTrigger(source, P1_RIGHT, brakeState, move), flags=QUEUED)

        self.at(*stickyTrigger(source, P1_LEFT, uncrouchState, move))
        self.at(*stickyTrigger(source, P1_RIGHT, uncrouchState, move))

        self.at(*endState(brakeState, unbrakeState))

        # self.crouch / elevator control
        self.at(*stickyTrigger(source, P1_DOWN, idleState, crouch))
        self.at(*stickyTrigger(source, P1_DOWN, crouchState, crouch), flags=BREAK)
        self.at(*stickyTrigger(source, P1_DOWN, uncrouchState, crouch), flags=BREAK)
        self.at(*endState(crouchState, uncrouch))

        self.at((source, P1_DOWN, BUTTONDOWN), walkState, crouch)

        self.at((source, P1_DOWN, BUTTONDOWN), fallRecoverState, crouch, flags=QUEUED)
        self.at((source, P1_DOWN, BUTTONDOWN), rollingState, crouch, flags=QUEUED)

        self.at(*endState(rollingState, uncrouch))


        # elevator control 
        #self.at((P1_UP, BUTTONDOWN), idleState, up)
        #self.at((P1_UP, BUTTONUP), upState, idle)


        # self.jumping
        self.at((source, P1_ACTION2, BUTTONDOWN), idleState, jump)
        self.at((source, P1_ACTION2, BUTTONDOWN), walkState, jump)

        # double jump
        self.at((source, P1_ACTION2, BUTTONDOWN), jumpingState, jump, flags=STUBBORN)

        self.at(*endState(jumpingState, checkFalling))
        self.at(*endState(fallingState, checkFalling))
        self.at(*endState(fallRecoverState, uncrouch))

        #self.at((STATE_VIRTUAL, STATE_FINISHED), jumpingState, checkFalling)
        #self.at((STATE_VIRTUAL, STATE_FINISHED), fallingState, checkFalling)
        #self.at((STATE_VIRTUAL, STATE_FINISHED), fallRecoverState,uncrouch)

        #self.at((P1_ACTION2, BUTTONUP), jumpingState, idle)

        #self.at((STATE_VIRTUAL, STATE_FINISHED), jumpingState, idle)


        # meh
        #self.at((STATE_VIRTUAL, STATE_FINISHED), idleState, idle)

        #self.push_state((idle, None), None)

        self.push_state(idleState(self, self.entity), None)

