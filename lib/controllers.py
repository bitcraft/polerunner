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
            ( this will effectively press player and stick to wall )
        if player jumps, allow for a 45 angle jump away from wall

"""


WALLJUMP_FORCE = 30
WALLGRAB_FORCE = 25
AIR_SPEED = 400
ACCELERATION = 2

MAXIMUM_SPEED = 400
INITIAL_WALK_SPEED = 100
RUN_SPEED = 200
SPRINT_SPEED = 220


class State(context.Context):

    # allows the state to clean up and sends 'state finished' event to the fsm
    def __exit__(self):
        self.exit()
        self.driver.process((self.__class__, STATE_VIRTUAL, STATE_FINISHED))

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    # allows the state to end cleanly
    def stop(self):
        try:
            self.driver.remove(self)
        except ValueError:
            print "FAILED TO REMOVE {}".format(self)

    # stops the state without calling the exit() method
    # also prevents the the end state trigger from being processed
    def abort(self):
        try:
            self.driver.remove(self, exit=False)
        except ValueError:
            print "FAILED TO REMOVE {}".format(self)

    def collide(self, *args, **kwargs):
        self.driver.process((self.__class__, STATE_VIRTUAL, COLLISION))

    def update(self, time):
        pass


class walkState(State):
    RIGHT = -10
    LEFT = 10
    feet = False  
 
    def init(self, trigger=None):
        self.body = self.driver.entity.body

        area = self.driver.entity.parent
        if trigger.cmd == P1_LEFT:
            self.driver.entity.avatar.flip = 1
            self.direction = self.LEFT
            self.maxSpeed = -MAXIMUM_SPEED
            # Max friction force on a flat surface = weight of body = mass * gravity
            self.maxFrictionForce = - self.body.mass * area.gravity[1]
        elif trigger.cmd == P1_RIGHT:
            self.driver.entity.avatar.flip = 0
            self.direction = self.RIGHT
            self.maxSpeed = MAXIMUM_SPEED
            # Max friction force on a flat surface = weight of body = mass * gravity
            self.maxFrictionForce = self.body.mass * area.gravity[1]

    def enter(self):
        force = (self.maxFrictionForce + self.maxSpeed * self.body.mass, 0)
        self.body.apply_force(force)


    def update(self, time):
        self.body.reset_forces()
        deltaVelocity = self.maxSpeed - self.body.velocity.x
        force = (self.maxFrictionForce + deltaVelocity * self.body.mass, 0)
        #self.body.apply_force(force)
        self.driver.entity.joints[1].rate = self.direction
        
        vel = abs(self.body.velocity.x)
        if vel < RUN_SPEED:
            self.driver.entity.avatar.play('walk')
        elif vel >= RUN_SPEED and vel < SPRINT_SPEED*.70:
            self.driver.entity.avatar.play('run')
        elif vel >= SPRINT_SPEED*.70:
            self.driver.entity.avatar.play('sprint')

    def exit(self):
        self.driver.entity.joints[1].rate = 0
        self.body.reset_forces()


class crouchState(State):
    def enter(self):
        self.driver.entity.avatar.play('crouch', loop_frame=4)
        body = self.driver.entity.body
        body.velocity.x = 0
        space = self.driver.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is body:
                break
        space.remove(old_shape)
        w, h = self.driver.entity.size
        shape = pymunk.Poly.create_box(body, size=(w, h/2))
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction
        self.driver.entity.parent.shapes[self.driver.entity] = shape
        body.position.y += 8
        space.add(shape)


class uncrouchState(State):
    def enter(self):
        self.driver.entity.avatar.play('uncrouch', callback=self.stop, loop=0)
        body = self.driver.entity.body
        body.velocity.x = 0
        space = self.driver.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is body:
                break
        space.remove(old_shape)
        w, h = self.driver.entity.size
        shape = pymunk.Poly.create_box(body, size=(w, h))
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction
        self.driver.entity.parent.shapes[self.driver.entity] = shape
        body.position.y -= 4
        space.add(shape)


class jumpingState(State):
    max_jumps = 2

    def init(self, trigger=None):
        self.body = self.driver.entity.body
        self.jumps = 0

    def enter(self):
        self.driver.entity.avatar.play('jumping')
        
        if not self.jumps == 0:
            return

        if self.driver.entity.grounded:
            self.jumps = 1
            self.body.apply_impulse((0, -self.driver.entity.jump_strength))
        else:
            if self.jumps <= self.max_jumps:
                self.jumps += 2
                self.body.apply_impulse((0, -self.driver.entity.jump_strength))

 
    def update(self, time):
        if self.body.velocity.y > 0:
            self.stop()

        if self.driver.entity.grounded:
            self.stop()


#  F A L L I N G  =============================================================
class fallingState(State):
    def enter(self):
        self.driver.entity.avatar.play('falling')
        self.body = self.driver.entity.body
 
    def update(self, time):
        if self.driver.entity.landed_previous or self.driver.entity.grounded:
            self.stop()


class fallRecoverState(State):
    def enter(self):
        self.driver.entity.avatar.play('crouch', loop_frame=4)
        self.body = self.driver.entity.body
        self.body.velocity.x /= 3.0
        space = self.driver.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is self.body:
                break
        space.remove(old_shape)
        w, h = self.driver.entity.size
        shape = pymunk.Poly.create_box(self.body, size=(w, h/2))
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction
        self.driver.entity.parent.shapes[self.driver.entity] = shape
        self.body.position.y += 8
        space.add(shape)

    def update(self, time):
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED:
            self.stop()


class deadState(State):
    def enter(self, trigger=None):
        self.driver.entity.avatar.play('die', loop_frame=2)


class airMoveState(State):
    RIGHT = 0
    LEFT = 1
   
    def init(self, trigger=None):
        self.body = self.driver.entity.body
        self.trigger = trigger

    def enter(self):
        if self.trigger.cmd == P1_LEFT:
            self.driver.entity.avatar.flip = self.LEFT
            self.direction = self.LEFT
            self.maxSpeed = -AIR_SPEED
        elif self.trigger.cmd == P1_RIGHT:
            self.driver.entity.avatar.flip = self.RIGHT
            self.direction = self.RIGHT
            self.maxSpeed = AIR_SPEED
        force = (self.maxSpeed * self.body.mass, 0)
        self.body.apply_force(force)

    def update(self, time):
        self.body.reset_forces()
        deltaVelocity = self.maxSpeed - self.body.velocity.x
        force = (deltaVelocity * self.body.mass, 0)
        self.body.apply_force(force)
        
        if self.driver.entity.landed_previous or self.driver.entity.grounded:
            self.stop()

        if self.body.velocity.y == 0:
            self.stop()

    def exit(self):
        self.body.reset_forces()
    

class idleState(State):
    def init(self, trigger=None):
        self.body = self.driver.entity.body

    def enter(self):
        self.driver.entity.avatar.play('idle')
        
    def update(self, time):
        pass


class brakeState(State):
    def enter(self):
        self.body = self.driver.entity.body
        self.driver.entity.avatar.play('brake', loop_frame=5)
        self.driver.entity.parent.emitSound('stop.wav', entity=self.driver.entity)

    def update(self, time):
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED:
            self.stop()


class unbrakeState(State):
    def enter(self):
        self.driver.entity.avatar.play('unbrake', callback=self.stop, loop=0)
        body = self.driver.entity.body


class wallGrabState(State):
    """
    allows player to stick to walls by applying horizontal force against a
    wall.  player will stick to wall by the friction of the wall

    TODO: calculate force needed to let play slide down wall slowly
    """

    RIGHT = 0
    LEFT = 1
 
    def init(self, trigger=None):
        # since init is called before this context is added to the stack, we
        # can safely get the values from the previous context, which in this
        # case will always be airMoveState
        self.trigger = self.driver.current_context.trigger
        self.body = self.driver.entity.body

    def enter(self):
        if self.trigger.cmd == P1_LEFT:
            self.maxSpeed = -WALLGRAB_FORCE

        elif self.trigger.cmd == P1_RIGHT:
            self.maxSpeed = WALLGRAB_FORCE

        force = (self.maxSpeed * self.body.mass, 0)
        self.body.apply_force(force)

    def update(self, time):
        self.body.reset_forces()
        deltaVelocity = self.maxSpeed - self.body.velocity.x
        force = (deltaVelocity * self.body.mass, 0)
        self.body.apply_force(force)
        
    def exit(self):
        self.body.reset_forces()


class wallJumpState(State):
    max_jumps = 2

    def init(self, trigger=None):
        # since init is called before this context is added to the stack, we
        # can safely get the values from the previous context, which in this
        # case will always be wallGrabState
        self.trigger = self.driver.current_context.trigger
        self.body = self.driver.entity.body

    def enter(self):
        if self.trigger.cmd == P1_LEFT:
            force = WALLJUMP_FORCE
        elif self.trigger.cmd == P1_RIGHT:
            force = -WALLJUMP_FORCE

        self.body.reset_forces()
        force = (force * self.body.mass, -self.driver.entity.jump_strength)
        self.body.apply_impulse(force)

    def update(self, time):
        if self.body.velocity.y > 0:
            self.stop()


class rollingState(State):
    def enter(self):
        self.original = self.driver.entity.avatar.animations['roll'].image
        self.original = self.original.convert_alpha()
        self.driver.entity.avatar.play('roll')
        self.angle = 0.0
        self.body = self.driver.entity.body
        space = self.driver.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is self.body:
                break
        space.remove(old_shape)
        w, h = self.driver.entity.size
        shape = pymunk.Circle(self.body, radius=8)
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction / 2.0
        self.driver.entity.parent.shapes[self.driver.entity] = shape
        space.add(shape)
        self.body.position.y += 4
        print shape.friction

    def update(self, time):
        self.angle -= 3
        colorkey = self.original.get_at((0,0))
        rotated = pygame.transform.rotozoom(self.original, self.angle, 1)
        self.driver.entity.avatar.animations['roll'].image = rotated
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED:
            self.driver.entity.avatar.animations['roll'].image = self.original
            self.stop()

    def exit(self):
        space = self.driver.entity.parent.space
        for shape in space.shapes:
            if shape.body is self.body:
                break
        shape.friction *= 2.0
        print "exit:", shape.friction


# =============================================================================
# context transition pickers

class transition(object):
    def __call__(self, *arg, **kwarg):
        return self.pick(*arg, **kwarg)

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def pick(self, driver, entity):
        pass


class dieT(transition):
    def pick(self, driver, entity):
        return deadState()


class fallingT(transition):
    def pick(self, driver, entity):
        return fallingState()


class checkFallingT(transition):
    def pick(self, driver, entity):
        body = entity.body
        print abs(entity.grounding['impulse'].y) / body.mass
        if abs(entity.grounding['impulse'].y) / body.mass == 0:
            return fallingState()
        else:
            return None


class idleT(transition):
    def pick(self, driver, entity):
        body = entity.body
        if body.velocity.y > 0:
            driver.append(idleState())
            return fallingState()

        return idleState()


class unbrakeT(transition):
    def pick(self, driver, entity):
        return unbrakeState()


class brakeT(transition):
    def pick(self, driver, entity):
        body = entity.body
        friction = body.velocity.x * body.mass * entity.parent.gravity[1]
        print "FRICTION", friction
        print body.velocity.x, RUN_SPEED, SPRINT_SPEED
        if abs(body.velocity.x) >= SPRINT_SPEED:
            return brakeState()
        else:
            return None


class moveT(transition):
    def pick(self, driver, entity):
        return walkState()


class crouchT(transition):
    def pick(self, driver, entity):
        body = entity.body
        if abs(body.velocity.x) > 1.2:
            return rollingState()
        else:
            return crouchState()


class uncrouchT(transition):
    def pick(self, driver, entity):
        return uncrouchState()


class upT(transition):
    def pick(self, driver, entity):
        return jumpingState()

class fallRecoverT(transition):
    def pick(self, driver, entity):
        body = entity.body
        if abs(body.velocity.x) >= SPRINT_SPEED:
            return rollingState()
        else:
            return fallRecoverState()

class jumpT(transition):
    def pick(self, driver, entity):
        return jumpingState()

class wallJumpT(transition):
    def pick(self, driver, entity):
        return wallJumpState()

class airmoveT(transition):
    def pick(self, driver, entity):
        return airMoveState()

class checkWallGrabT(transition):
    def pick(self, driver, entity):
        return wallGrabState()

die = dieT()
idle = idleT()
brake = brakeT()
unbrake = unbrakeT()
move = moveT()
crouch = crouchT()
uncrouch = uncrouchT()
up = upT()
fallRecover = fallRecoverT()
jump = jumpT()
checkFalling = checkFallingT()
walljump = wallJumpT()
airmove = airmoveT()
checkWallGrab = checkWallGrabT()
fall = fallingT()


# =============================================================================
# transition formulas

# context will be automatically canceled when the button is released
def toggle(source, trigger, ctx, picker):
    return (source, trigger, BUTTONDOWN), ctx, picker, (source, trigger, BUTTONUP)

# new_ctx will be run whenever old_ctx finishes
def endState(ctx, picker):
    return (ctx, STATE_VIRTUAL, STATE_FINISHED), None, picker

# new_context will be run when transitioning from ctx0 to ctx1
def inject(ctx0, ctx1, picker):
    return (ctx0, STATE_VIRTUAL, STATE_FINISHED), ctx1, picker

# new_ctx will be run when there is a collision during old_ctx
# this formula is not completely supported yet
def collision(ctx, picker):
    return (ctx, STATE_VIRTUAL, COLLISION), ctx, picker

#
# =============================================================================

class HeroController(lib2d.fsa.fsa):

    def program(self, source):

        # walking
        self.at(*toggle(source, P1_LEFT, idleState, move))
        self.at(*toggle(source, P1_RIGHT, idleState, move))

        # brake animation after a sprint
        self.at(*inject(walkState, idleState, brake))

        # allow walking to cancel from walking or braking
        self.at(*toggle(source, P1_LEFT, walkState, move),flags=BREAK)
        self.at(*toggle(source, P1_RIGHT, walkState, move),flags=BREAK)
        self.at(*toggle(source, P1_LEFT, unbrakeState, move),flags=QUEUED)
        self.at(*toggle(source, P1_RIGHT, unbrakeState, move),flags=QUEUED)
        self.at(*toggle(source, P1_LEFT, brakeState, move),flags=QUEUED)
        self.at(*toggle(source, P1_RIGHT, brakeState, move),flags=QUEUED)

        # allow uncrouch animation to be canceled (skipped)
        self.at(*toggle(source, P1_LEFT, uncrouchState, move))
        self.at(*toggle(source, P1_RIGHT, uncrouchState, move))

        # play unbrake animation after the brake animation
        self.at(*endState(brakeState, unbrake))


        # moving in the air
        self.at(*toggle(source, P1_LEFT, jumpingState, airmove))
        self.at(*toggle(source, P1_RIGHT, jumpingState, airmove))
        self.at(*toggle(source, P1_LEFT, fallingState, airmove))
        self.at(*toggle(source, P1_RIGHT, fallingState, airmove))

        # allow air animation to cancel on left or right
        self.at(*toggle(source, P1_LEFT, airMoveState, airmove), flags=BREAK)
        self.at(*toggle(source, P1_RIGHT, airMoveState, airmove), flags=BREAK)

        # if colliding during airmove, then check if player can grab wall
        #self.at(*collision(airMoveState, checkWallGrab), flags=BREAK)

        # wall jumping
        self.at((source, P1_ACTION2, BUTTONDOWN), wallGrabState, walljump, flags=BREAK)


        # crouch
        self.at(*toggle(source, P1_DOWN, idleState, crouch))

        # roll
        self.at((source, P1_DOWN, BUTTONDOWN), walkState, crouch)

        # allow crouching to cancel into crouching
        #self.at(*toggle(source, P1_DOWN, crouchState, crouch), flags=BREAK)
        #self.at(*toggle(source, P1_DOWN, uncrouchState, crouch), flags=BREAK)

        # play uncrouch animation after crouching
        self.at(*endState(crouchState, uncrouch))

        # roll recovers after big jumps
        #self.at((source, P1_DOWN, BUTTONDOWN), fallRecoverState, crouch)
        #self.at((source, P1_DOWN, BUTTONDOWN), rollingState, crouch)

        # play uncrouch animation after a roll
        self.at(*endState(rollingState, uncrouch))


        # jumping
        self.at((source, P1_ACTION2, BUTTONDOWN), idleState, jump)
        self.at((source, P1_ACTION2, BUTTONDOWN), walkState, jump)

        # double jump
        #self.at((source, P1_ACTION2, BUTTONDOWN), jumpingState, jump, flags=BREAK)
        #self.at((source, P1_ACTION2, BUTTONDOWN), fallingState, jump, flags=BREAK)

        # falling after a jump
        #self.at(*endState(jumpingState, fall))


    def primestack(self):
        # set our initial context
        self.append(idleState())


    def reset(self):
        for ctx in reversed(self._stack):
            self.remove(ctx)

        self.time = 0
        self.holds = {}
        self.move_history = []
        self.last_context = None
        self.primestack()
