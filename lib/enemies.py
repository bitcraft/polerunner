from entity import Entity
from pygoap.agent import GoapAgent
from pygoap.actions import *
from pygoap.goals import *
from lib2d.buttons import *

import random



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
 

#
# =============================================================================


class LaserRobot(Entity):
    mass = 7
    size = (16,32,16)
    moving_speed = 65

    def build_agent(self):
        agent = GoapAgent()
        agent.add_action(MoveAnywhere())
        #agent.add_action(Shoot())
        agent.add_goal(SimpleGoal(exterminate_human=True))
        agent.add_goal(SimpleGoal(moving=True))
        return agent


class HoverBot(Entity):
    sounds = ["hover0.wav", "whiz0.wav", "startupfail1.wav"]

    time_update = True
    time = 0
    last_hover = 0


    def hover(self, multiplier):
        body = self.parent.getBody(self)

        if multiplier >= 80:
            self.parent.emitSound("startupfail1.wav", ttl=1000, thing=self)
        elif body.vel.z > .2:
            self.parent.emitSound("whiz0.wav", ttl=400, thing=self)
        else:
            self.parent.emitSound("hover0.wav", ttl=100, thing=self)


        self.avatar.play("hover")
        self.last_hover = self.time
        body.acc.z -= self.parent.physicsgroup.gravity_delta.z * multiplier


    def update(self, time):
        """
        do some cool hackery here
        
        we assume the lbrary is updating the physics 5x to one draw and the
        fps is locked at 40, so we can easily simulate thrusters levitating
        the robot.
        """

        body = self.parent.getBody(self)

        self.time += time
        if self.time >= self.last_hover + 300:
            self.avatar.play("fall")

        # if true we are falling
        if body.vel.z > .05:

            # test if robot is hovering over the ground
            # find how far away the ground is (not a great way to do this)
            distance = 16
            bbox = body.bbox.copy()
            bbox.move(0,0,distance)

            while self.parent.physicsgroup.testCollision(bbox):
                distance -= 1
                bbox = body.bbox.copy()
                bbox.move(0,0,distance)


            freq = round(distance/16.0 * 3)

            # make the robot a bit wonky
            if random.randint(0,freq) == 0:

                if distance == 16:
                    self.hover(2)
                else:
                    body.vel.z = body.vel.z / 2.0
                    body.acc.z = 0
                    self.hover(40)

        elif body.vel.z == 0:
            bbox = body.bbox.copy()
            bbox.move(0,0,1)

            if self.parent.physicsgroup.testCollision(bbox):
                self.hover(80)

        if body.vel.z < -.1:
            body.vel.z = -.1
