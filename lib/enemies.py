from entity import Entity
from pygoap.agent import GoapAgent
from pygoap.actions import *
from pygoap.goals import *
from lib2d.buttons import *

import pymunk
import random
import math



# =============================================================================
# ACTION CLASSES FOR ENEMY AI

class PathfindAction(ActionContext):
    def update(self, time):
        super(move_action, self).update(time)
        if self.caller.position[1] == self.endpoint:
            self.finish()
        else:
            env = self.caller.environment
            path = env.pathfind(self.caller.position[1], self.endpoint)
            path.pop() # this will always the the starting position
            env.move(self.caller, (env, path.pop()))


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
        self.entity = self.caller.environment.get_entity(self.caller)
        self.body = self.entity.parent.getBody(self.entity)
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


class ShootAction(CalledOnceContext):
    def enter(self):
        self.entity = self.caller.environment.get_entity(self.caller)
        self.entity.avatar.play('shoot') 
        print "pow"


class MoveAction(ActionContext):
    def enter(self):
        self.entity = self.caller.environment.get_entity(self.caller)
        self.body = self.entity.parent.getBody(self.entity)
        self.direction = random.choice((P1_LEFT, P1_RIGHT))
        self.update_forces()
        force = (self.maxFrictionForce + self.maxSpeed * self.body.mass, 0)
        self.body.apply_force(force)
        self.entity.avatar.play('idle')

    def update_forces(self):
        if self.direction == P1_LEFT:
            self.entity.avatar.flip = 0
            self.maxSpeed = -self.entity.moving_speed
            self.maxFrictionForce = -self.body.mass * self.entity.parent.gravity[1]
        elif self.direction == P1_RIGHT:
            self.entity.avatar.flip = 1
            self.maxSpeed = self.entity.moving_speed
            self.maxFrictionForce = self.body.mass * self.entity.parent.gravity[1]

    def update(self, time):
        if not random.randint(0, 500):
            self.finish()

        self.body.reset_forces()
        deltaVelocity = self.maxSpeed - self.body.velocity.x
        force = (self.maxFrictionForce + deltaVelocity * self.body.mass, 0)
        self.body.apply_force(force)
        

class MoveAnywhere(ActionBuilder):
    def get_actions(self, caller, memory):
        action = MoveAction(caller)
        action.effects.append(SimpleGoal(moving=True))
        yield action

class Shoot(ActionBuilder):
    def get_actions(self, caller, memory):
        action = ShootAction(caller)
        action.effects.append(SimpleGoal(exterminate_human=True))
        yield action

class Thrust(ActionBuilder):
    def get_actions(self, caller, memory):
        entity = caller.environment.get_entity(caller)
        body = entity.parent.getBody(entity)
        if body.velocity.y > 0 or entity.grounded:
            action = HoverAction(caller)
            action.effects.append(SimpleGoal(flying=True))
            yield action

        


#
# =============================================================================


class LaserRobot(Entity):
    mass = 7
    size = (16,32,16)
    moving_speed = 65

    def build_agent(self):
        self.name = "sad"
        agent = GoapAgent()
        agent.add_action(MoveAnywhere())
        #agent.add_action(Shoot())
        agent.add_goal(SimpleGoal(exterminate_human=True))
        agent.add_goal(SimpleGoal(moving=True))
        #return agent


class HoverBot(Entity):
    sounds = ["hover0.wav", "whiz0.wav", "startupfail1.wav"]
    mass = 1
    size = (16,16,16)
    moving_speed = 40

    def build_agent(self):
        agent = GoapAgent()
        agent.add_action(Thrust())
        agent.add_goal(SimpleGoal(flying=True))
        return agent

    def build_shapes(self, body):
        return [pymunk.Circle(body, self.size[0]/2)]
