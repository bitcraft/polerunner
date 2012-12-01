from entity import Entity
from actions import *
from pygoap.agent import GoapAgent
from pygoap.actions import *
from pygoap.goals import *
from lib2d.buttons import *

import pymunk
import random
import math



# =============================================================================
# ACTION CLASSES FOR ENEMY AI

class ShootAction(CalledOnceContext):
    def enter(self):
        self.entity = self.parent.entity
        self.entity.avatar.play('shoot') 
        print "pow"


# =============================================================================
# ACTION BUILDERS FOR PYGOAP ENEMY AI 

class MoveAnywhere(ActionBuilder):
    def get_actions(self, parent, memory):
        action = MoveAction(parent)
        action.effects.append(SimpleGoal(moving=True))
        yield action

class Shoot(ActionBuilder):
    def get_actions(self, parent, memory):
        action = ShootAction(parent)
        action.effects.append(SimpleGoal(exterminate_human=True))
        yield action

class Thrust(ActionBuilder):
    def get_actions(self, parent, memory):
        entity = parent.entity
        if entity.body.velocity.y > 0 or entity.grounded:
            action = HoverAction(parent)
            action.effects.append(SimpleGoal(flying=True))
            yield action


# =============================================================================
# ENEMY DEFINITIONS

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

    def load(self):
        r = self.size[0]/ 2
        m = pymunk.moment_for_circle(self.mass, r, r)

        body = pymunk.Body(self.mass, m)
        body.position = self.position

        shape = pymunk.Circle(body, r)
        shape.friction = 1.0

        self.bodies = [body]
        self.shapes = [shape]
