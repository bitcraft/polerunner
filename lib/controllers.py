"""
command tree for the main character
"""

from lib2d.buttons import *
from lib2d.fsa.flags import *
from lib2d import context
import lib2d, pygame, pymunk, math

"""
GOALS FOR PLAYER CONTROL

metroid / ninja / n

* fast paced actions
* wall jumps and grabs
* ducking rolls
* grabbing ceilings
* ladders
* elevators
* double jumps
* lots of animations
* double tap dives
* prone
* mirror's edge!!!

don't try to be too realistic, make it really fun!

wall jumps:
    find if collision is on side of wall
    if wall has a high friction
        if player is pressing away from the wall
            apply horizontal force against wall
            ( this will effectively press play and stick to wall )
        if player jumps, allow for a 45 angle jump away from wall

"""



INITIAL_WALK_SPEED = 2.5
ACCELERATION = 2
RUN_SPEED = 40 #80
SPRINT_SPEED = 150
#WALK_SPEED_INCREMENT = .5
STOPPING_FRICTION = 0.994
ROLLING_FRICTION = 0.99


class State(context.Context):
    def __init__(self, driver, entity, *args, **kwargs):
        context.Context.__init__(self, driver)
        self.entity = entity
        self.cmd = None

    def abort(self):
        try:
            self.driver.remove(self)
        except:
            pass

    def terminate(self, *args, **kwargs):
        self.driver.process((self.__class__, STATE_VIRTUAL, STATE_FINISHED))

    def update(self, time):
        pass


class walkState(State):
    RIGHT = 0
    LEFT = 1
   
    def init(self, cmd=None):
        self.body = self.entity.parent.getBody(self.entity)
        self.cmd = cmd[1:]

    def enter(self):
        area = self.entity.parent
        if self.cmd[0] == P1_LEFT:
            self.entity.avatar.flip = self.LEFT
            self.direction = self.LEFT
            self.maxSpeed = - SPRINT_SPEED
            # Max friction force on a flat surface = weight of body = mass * gravity
            self.maxFrictionForce = - self.body.mass * area.gravity[1]
        elif self.cmd[0] == P1_RIGHT:
            self.entity.avatar.flip = self.RIGHT
            self.direction = self.RIGHT
            self.maxSpeed = SPRINT_SPEED
            # Max friction force on a flat surface = weight of body = mass * gravity
            self.maxFrictionForce = self.body.mass * area.gravity[1]
        force = (self.maxFrictionForce + self.maxSpeed * self.body.mass, 0)
        self.body.apply_force(force)

    def update(self, time):
        self.body.reset_forces()
        deltaVelocity = self.maxSpeed - self.body.velocity.x
        force = (self.maxFrictionForce + deltaVelocity * self.body.mass, 0)
        self.body.apply_force(force)
        
        vel = abs(self.body.velocity.x)
        if vel < RUN_SPEED:
            self.entity.avatar.play('walk')
        elif vel >= RUN_SPEED and vel < SPRINT_SPEED:
            self.entity.avatar.play('run')
        elif vel >= SPRINT_SPEED:
            self.entity.avatar.play('sprint')

    def exit(self):
        self.body.reset_forces()


class crouchState(State):
    def enter(self):
        self.entity.avatar.play('crouch', loop_frame=4)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = 0
        space = self.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is body:
                break
        space.remove(old_shape)
        w, h = self.entity.size
        shape = pymunk.Poly.create_box(body, size=(w, h/2))
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction
        self.entity.parent.shapes[self.entity] = shape
        body.position.y += 8
        space.add(shape)


class uncrouchState(State):
    def enter(self):
        self.entity.avatar.play('uncrouch', callback=self.abort, loop=0)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = 0
        space = self.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is body:
                break
        space.remove(old_shape)
        w, h = self.entity.size
        shape = pymunk.Poly.create_box(body, size=(w, h))
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction
        self.entity.parent.shapes[self.entity] = shape
        body.position.y -= 4
        space.add(shape)


class jumpingState(State):
    max_jumps = 2

    def init(self, cmd=None):
        self.jumps = 0
        if cmd is None:
            return 

    def enter(self):
        area = self.entity.parent
        self.body = self.entity.parent.getBody(self.entity)

        if abs(self.body.velocity.x) > RUN_SPEED:
            self.entity.avatar.play('jumping')

        if self.entity.grounded:
            self.jumps = 1
            self.body.apply_impulse((0, -self.entity.jump_strength))
        else:
            if self.jumps <= self.max_jumps:
                self.jumps += 2
                self.body.apply_impulse((0, -self.entity.jump_strength))


    def update(self, time):
        if self.body.velocity.y > 0:
            self.abort()


class fallRecoverState(State):
    def enter(self):
        self.entity.avatar.play('crouch', loop_frame=4)
        self.body = self.entity.parent.getBody(self.entity)
        self.body.velocity.x /= 3.0
        space = self.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is self.body:
                break
        space.remove(old_shape)
        w, h = self.entity.size
        shape = pymunk.Poly.create_box(self.body, size=(w, h/2))
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction
        self.entity.parent.shapes[self.entity] = shape
        self.body.position.y += 8
        space.add(shape)

    def update(self, time):
        self.body.velocity.x *= STOPPING_FRICTION
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED/4.0:
            self.abort()


class deadState(State):
    def enter(self, cmd):
        self.entity.avatar.play('die', loop_frame=2)


class upState(State):
    pass

class runState(State):
    pass

class sprintState(State):
    pass


class idleState(State):
    def init(self, cmd=None):
        self.body = self.entity.parent.getBody(self.entity)

    def enter(self):
        self.entity.avatar.play('idle')
        
    def update(self, time):
        pass


class brakeState(State):
    def enter(self):
        self.entity.avatar.play('brake', loop_frame=5)
        self.body = self.entity.parent.getBody(self.entity)
        self.entity.parent.emitSound('stop.wav', entity=self.entity)

    def update(self, time):
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED:
            self.abort()


class unbrakeState(State):
    def enter(self):
        self.entity.avatar.play('unbrake', callback=self.abort, loop=0)
        body = self.entity.parent.getBody(self.entity)
        body.velocity.x = 0


class fallingState(State):
    def enter(self):
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


class rollingState(State):
    def enter(self):
        self.original = self.entity.avatar.animations['roll'].image.convert_alpha()
        self.entity.avatar.play('roll')
        self.angle = 0.0
        self.body = self.entity.parent.getBody(self.entity)
        space = self.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is self.body:
                break
        space.remove(old_shape)
        w, h = self.entity.size
        shape = pymunk.Circle(self.body, radius=8)
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction
        self.entity.parent.shapes[self.entity] = shape
        space.add(shape)
        self.body.position.y += 4

    def update(self, time):
        self.angle -= 3
        colorkey = self.original.get_at((0,0))
        rotated = pygame.transform.rotozoom(self.original, self.angle, 1)
        self.entity.avatar.animations['roll'].image = rotated
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED:
            self.entity.avatar.animations['roll'].image = self.original
            self.abort()


# =============================================================================
# context function pickers

class transition(object):
    def __call__(self, *arg, **kwarg):
        return self.pick(*arg, **kwarg)

    def pick(self, driver, entity):
        pass

class dieT(transition):
    def pick(self, driver, entity):
        return deadState(driver, entity)


class checkFallingT(transition):
    def pick(self, driver, entity):
        if entity.grounded:
            return fallRecoverState(driver, entity)

        body = entity.parent.getBody(entity)

        if body.velocity.y > 0:
            return fallingState(driver, entity)

        elif body.velocity.y < 0:
            return fallingState(driver, entity)

        else:
            return fallRecoverState(driver, entity)


class idleT(transition):
    def pick(self, driver, entity):
        body = entity.parent.getBody(entity)
        print body.velocity.y
        if body.velocity.y > 0:
            driver.append(idleState(driver, entity))
            return fallingState(driver, entity)

        return idleState(driver, entity)


class brakeT(transition):
    def pick(self, driver, entity):
        body = entity.parent.getBody(entity)
        vel_x = abs(body.velocity.x)

        if 0 < vel_x < SPRINT_SPEED:
            body.velocity.x = 0.0
            return None
        elif vel_x >= SPRINT_SPEED:
            return brakeState(driver, entity)


class moveT(transition):
    def pick(self, driver, entity):
        return walkState(driver, entity)


class crouchT(transition):
    def pick(self, driver, entity):
        body = entity.parent.getBody(entity)
        if abs(body.velocity.x) > 1.2:
            return rollingState(driver, entity)
        else:
            return crouchState(driver, entity)


class uncrouchT(transition):
    def pick(self, driver, entity):
        return uncrouchState(driver, entity)


class upT(transition):
    def pick(self, driver, entity):
        return jumpingState(driver, entity)

class fallRecoverT(transition):
    def pick(self, driver, entity):
        body = entity.parent.getBody(entity)
        print body.velocity.x
        if abs(body.velocity.x) >= SPRINT_SPEED:
            return rollingState(driver, entity)
        else:
            return fallRecoverState(driver, entity)

class jumpT(transition):
    def pick(self, driver, entity):
        return jumpingState(driver, entity)


def stickyTrigger(source, trigger, context, picker):
    return (source, trigger, BUTTONDOWN), context, picker, (source, trigger, BUTTONUP)

def stickyHeldTrigger(source, trigger, context, picker):
    return (source, trigger, BUTTONHELD), context, picker, (trigger, BUTTONUP)

def endState(context, new_context):
    return (context, STATE_VIRTUAL, STATE_FINISHED), context, new_context

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

    def program(self, source):

        # position and movement
        self.at(*stickyTrigger(source, P1_LEFT, idleState, move))
        self.at(*stickyTrigger(source, P1_RIGHT, idleState, move))

        self.at(*endState(walkState, brake))

        self.at(*stickyTrigger(source, P1_LEFT, walkState, move),flags=BREAK)
        self.at(*stickyTrigger(source, P1_RIGHT, walkState, move),flags=BREAK)
        self.at(*stickyTrigger(source, P1_LEFT, unbrakeState, move),flags=BREAK)
        self.at(*stickyTrigger(source, P1_RIGHT, unbrakeState, move),flags=BREAK)
        self.at(*stickyTrigger(source, P1_LEFT, brakeState, move),flags=BREAK)
        self.at(*stickyTrigger(source, P1_RIGHT, brakeState, move),flags=BREAK)

        self.at(*stickyTrigger(source, P1_LEFT, uncrouchState, move))
        self.at(*stickyTrigger(source, P1_RIGHT, uncrouchState, move))

        self.at(*endState(brakeState, unbrakeState))


        # self.crouch / elevator control
        self.at(*stickyTrigger(source, P1_DOWN, idleState, crouch))
        self.at(*stickyTrigger(source, P1_DOWN, crouchState, crouch), flags=BREAK)
        self.at(*stickyTrigger(source, P1_DOWN, uncrouchState, crouch), flags=BREAK)
        self.at(*endState(crouchState, uncrouch))

        self.at((source, P1_DOWN, BUTTONDOWN), walkState, crouch)

        #self.at((source, P1_DOWN, BUTTONDOWN), fallRecoverState, crouch)
        #self.at((source, P1_DOWN, BUTTONDOWN), rollingState, crouch)

        self.at(*endState(rollingState, uncrouch))

        # elevator control 
        #self.at((P1_UP, BUTTONDOWN), idleState, up)
        #self.at((P1_UP, BUTTONUP), upState, idle)


        # self.jumping
        self.at((source, P1_ACTION2, BUTTONDOWN), idleState, jump)
        self.at((source, P1_ACTION2, BUTTONDOWN), walkState, jump)


        # double jump
        #self.at((source, P1_ACTION2, BUTTONDOWN), jumpingState, jump, flags=STUBBORN)
        #self.at((source, P1_ACTION2, BUTTONDOWN), fallingState, jump, flags=STUBBORN)

        self.at(*endState(jumpingState, checkFalling))
        #self.at(*endState(fallingState, checkFalling))
        #self.at(*endState(fallRecoverState, uncrouch))

        # sanity, also falling
        self.at(*endState(idleState, idle))

    def primestack(self):
        # set our initial context
        self.append(idleState(self, self.entity))


    def reset(self):
        print "RESET"
        for context in reversed(self._stack):
            print "REMOVE", context
            self.remove(context)

        self.time = 0
        self.holds = {}
        self.move_history = []
        self.primestack()
