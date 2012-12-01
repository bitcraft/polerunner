"""
All actions that can be executed by the player or NPCS will be added here.

These can be used with a pygoap context manager or lib2d fsm.
Clients who wish to use them may import them in their module.
"""
from pygoap import ActionContext
from lib2d.fsm import State
from lib2d.buttons import *
import pymunk



class HoverAction(ActionContext):
    """
    hover in air and attempt to stay in one spot

    includes some physics calculations that let body slowly come to stop
    """

    max_power = 100
    max_horiz_force = 40
    hover_height = 32.0
    tolerance = 2.0

    def enter(self):
        self.entity = self.parent.entity
        self.body = self.entity.body
        self.intended_position = pymunk.Vec2d(self.body.position)
        self.space = self.entity.parent.space

        for shape in self.space.shapes:
            if shape.body is self.body:
                self.shape = shape
                break

        self.weight = self.body.mass * self.entity.parent.gravity[1]
        self.body.apply_impulse((0, -self.weight*.8))
        self.entity.avatar.play('hover')

    def update(self, time):

        if round(self.body.velocity.y) >= 0:
            gravity = self.entity.parent.gravity[1]
            start = self.body.position
            end = self.body.position + (4, self.hover_height)
            height = -1
            for hit in self.space.segment_query(start, end):
                if hit.shape is not self.shape:
                    height = self.hover_height - hit.get_hit_distance()

            # object is now above the floating height
            if height == -1:
                power = 0
            else:
                power = -(height / self.hover_height) * self.max_power * gravity
        else:
            power = 0

        forces = self.body.force + (self.body.velocity * self.body.mass)
        accel = forces / self.body.mass
        deaccel = -self.max_horiz_force / self.body.mass

        try:
            t = self.body.velocity / -deaccel
            disp = self.body.velocity * t + .5 * deaccel * t * t
        except ZeroDivisionError:
            disp = pymunk.Vec2d(0,0)

        dist = self.intended_position - self.body.position

        if abs(dist.x) < self.tolerance:
            if self.body.velocity.x > 0:
                self.body.velocity.x = 0
            v = 0

        elif abs(disp.x) >= abs(dist.x):
            self.body.reset_forces()
            if self.body.velocity.x > 0:
                v = -self.max_horiz_force
            elif self.body.velocity.x < 0:
                v = self.max_horiz_force
            else:
                v = 0
        else:
            if dist.x > self.tolerance:
                v = self.max_horiz_force
            elif dist.x < self.tolerance:
                v = -self.max_horiz_force
            else:
                v = 0


        new_force = pymunk.Vec2d(v, power) * self.body.mass
        delta_force = self.body.force - new_force

        self.body.reset_forces()
        self.body.apply_force(new_force)

        if self.body.velocity.y > 0:
            self.entity.avatar.play('hover')
        elif self.entity.grounded:
            #self.finish()
            pass
        else:
            self.entity.avatar.play('idle')


class MoveAction(State):
    """
    Move left or right for wheel-based-movement entities
    This includes the player and most NPC/enemies
    """

    def enter(self):
        self.body = self.parent.entity.body
        self.motor = self.parent.entity.motor
        self.direction = self.trigger.cmd

        if self.direction == P1_LEFT:
            self.parent.entity.avatar.flip = 1
            self.maxSpeed = self.parent.entity.max_speed

        elif self.direction == P1_RIGHT:
            self.parent.entity.avatar.flip = 0
            self.maxSpeed = -self.parent.entity.max_speed

        self.motor.rate = self.maxSpeed

    def update(self, time):
        vel = abs(self.body.velocity.x)
        speed = abs(self.maxSpeed)
        if 0 < vel < speed / 2:
            self.parent.entity.avatar.play('walk')
        elif vel >= speed / 2 and vel < speed*2:
            self.parent.entity.avatar.play('run')

    def exit(self):
        self.motor.rate = 0

class CrouchAction(State):
    def enter(self):
        entity = self.parent.entity
        body = self.parent.entity.body

        entity.avatar.play('crouch', loop_frame=4)

        w, h = entity.size
        old_shape = entity.shapes[0]
        entity.parent.space.remove(entity.shapes)

        shape = pymunk.Poly.create_box(body, size=(w, h/2))
        shape.collision_type = 0
        shape.friction = old_shape.friction

        entity.shapes = [shape]
        body.position += (0, 16)
        body.velocity.x = 0
        entity.parent.space.add(shape)

class UncrouchAction(State):
    def enter(self):
        self.parent.entity.avatar.play('uncrouch', callback=self.stop, loop=0)
        self.parent.entity.position -= (0, 8)
        self.parent.entity.rebuild()

class JumpAction(State):
    max_jumps = 2

    def init(self):
        self.body = self.parent.entity.body
        self.jumps = 0

    def enter(self):
        self.parent.entity.avatar.play('jumping')
        
        if not self.jumps == 0:
            return

        if self.parent.entity.grounded:
            self.jumps = 1
            self.body.apply_impulse((0, -self.parent.entity.jump_strength))
        else:
            if self.jumps <= self.max_jumps:
                self.jumps += 2
                self.body.apply_impulse((0, -self.parent.entity.jump_strength))

 
    def update(self, time):
        if self.body.velocity.y > 0:
            self.stop()

        if self.parent.entity.grounded:
            self.stop()


class FallAction(State):
    def enter(self):
        self.parent.entity.avatar.play('falling')
 
    def update(self, time):
        if self.parent.entity.landed_previous or self.parent.entity.grounded:
            self.stop()


class FallRecoverAction(State):
    def enter(self):
        self.parent.entity.avatar.play('crouch', loop_frame=4)
        self.body = self.parent.entity.body
        self.body.velocity.x /= 3.0
        space = self.parent.entity.parent.space
        for old_shape in space.shapes:
            if old_shape.body is self.body:
                break
        space.remove(old_shape)
        w, h = self.parent.entity.size
        shape = pymunk.Poly.create_box(self.body, size=(w, h/2))
        shape.collision_type = old_shape.collision_type
        shape.friction = old_shape.friction
        self.parent.entity.parent.shapes[self.parent.entity] = shape
        self.body.position.y += 8
        space.add(shape)

    def update(self, time):
        if abs(self.body.velocity.x) < INITIAL_WALK_SPEED:
            self.stop()


class DieAction(State):
    def enter(self):
        self.parent.entity.avatar.play('die', loop_frame=2)


class AirMoveAction(State):
    RIGHT = 0
    LEFT = 1
   
    def init(self):
        self.body = self.parent.entity.body

    def enter(self):
        if self.trigger.cmd == P1_LEFT:
            self.parent.entity.avatar.flip = self.LEFT
            self.maxSpeed = -self.parent.entity.max_speed * 3
        elif self.trigger.cmd == P1_RIGHT:
            self.parent.entity.avatar.flip = self.RIGHT
            self.maxSpeed = self.parent.entity.max_speed * 3
        force = (self.maxSpeed * self.body.mass, 0)
        self.body.apply_force(force)

    def update(self, time):
        self.body.reset_forces()
        deltaVelocity = self.maxSpeed - self.body.velocity.x
        force = (deltaVelocity * self.body.mass, 0)
        self.body.apply_force(force)
        
        if self.parent.entity.landed_previous or self.parent.entity.grounded:
            self.stop()

        if self.body.velocity.y == 0:
            self.stop()

    def exit(self):
        self.body.reset_forces()
    

class IdleAction(State):
    def enter(self):
        self.parent.entity.avatar.play('idle')
        
class BrakeAction(State):
    def enter(self):
        self.body = self.parent.entity.body
        self.parent.entity.avatar.play('brake', loop_frame=5)
        self.parent.entity.parent.emitSound('stop.wav', entity=self.parent.entity)

    def update(self, time):
        if abs(self.body.velocity.x) < 1:
            self.stop()


class UnbrakeAction(State):
    def enter(self):
        self.parent.entity.avatar.play('unbrake', callback=self.stop, loop=0)
        body = self.parent.entity.body


class wallGrabState(State):
    """
    allows player to stick to walls by applying horizontal force against a
    wall.  player will stick to wall by the friction of the wall

    TODO: calculate force needed to let play slide down wall slowly
    """

    RIGHT = 0
    LEFT = 1
 
    def init(self):
        # since init is called before this context is added to the stack, we
        # can safely get the values from the previous context, which in this
        # case will always be airMoveState
        self.trigger = self.parent.current_context.trigger
        self.body = self.parent.entity.body

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

    def init(self):
        # since init is called before this context is added to the stack, we
        # can safely get the values from the previous context, which in this
        # case will always be wallGrabState
        self.trigger = self.parent.current_context.trigger
        self.body = self.parent.entity.body

    def enter(self):
        if self.trigger.cmd == P1_LEFT:
            force = WALLJUMP_FORCE
        elif self.trigger.cmd == P1_RIGHT:
            force = -WALLJUMP_FORCE

        self.body.reset_forces()
        force = (force * self.body.mass, -self.parent.entity.jump_strength)
        self.body.apply_impulse(force)

    def update(self, time):
        if self.body.velocity.y > 0:
            self.stop()


class RollAction(State):
    def enter(self):
        self.original = self.parent.entity.avatar.animations['roll'].image
        self.original = self.original.convert_alpha()
        self.parent.entity.avatar.play('roll')

        entity = self.parent.entity
        old_body = entity.body
        entity.parent.space.remove(entity.bodies, entity.shapes, entity.joints)

        w, h = entity.size
        r = w * .5
        m = pymunk.moment_for_circle(entity.mass*5, 0, r)

        body = pymunk.Body(entity.mass, m)
        body.position = old_body.position + (0, r*2)
        body.velocity = old_body.velocity

        shape = pymunk.Circle(body, r)
        shape.friction = .5

        entity.bodies = [body]
        entity.shapes = [shape]
        entity.joints = []
        entity.parent.space.add(entity.bodies, entity.shapes)

        self.body = body

    def update(self, time):
        self.body.velocity.x *= .998
        if abs(self.body.velocity.x) < 30:
            self.parent.entity.avatar.animations['roll'].image = self.original
            self.body.reset_forces()
            self.body.velocity.x = 0
            self.stop()
