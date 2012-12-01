import res
from pathfinding.astar import Node
from objects import GameObject
from pygame import Rect
from pathfinding import astar
from lib2d.signals import *
from lib2d.zone import Zone
from lib2d.sound import Sound
from pygoap.environment import Environment, ObjectBase
from pygoap.precepts import *
import math

import pymunk

cardinalDirs = {"north": math.pi*1.5,
                "east": 0.0,
                "south": math.pi/2,
                "west": math.pi}

def toChipPoly(rect):
    return (rect.topleft, rect.topright, rect.bottomright, rect.bottomleft)


class AbstractArea(GameObject):
    pass


class AreaEnvironment(Environment):
    def __init__(self, area):
        Environment.__init__(self)
        self.area = area
        self.last_scan = 99999

    def add(self, agent, entity):
        agent.entity = entity
        Environment.add(self, agent)

    def model_vision(self, precept, origin, terminus):
        return precept

    def model_sound(self, precept, origin, terminus):
        return precept

    def update(self, time):
        self.last_scan += 1
        if self.last_scan > 200:
            [ self.look(agent) for agent in self.agents ]
            self.last_scan = 0

        Environment.update(self, time)

    def look(self, caller, direction=None, distance=None):
        """
        Simulate vision by sending precepts to the caller.
        """

        model = self.model_precept

        for entity in self.entities:
            precept = PositionPrecept(entity, self.get_position(entity))
            caller.process(model(precept, caller))

    def get_position(self, agent):
        return tuple(agent.entity.body.position)

    def objects_at(self, position):
        """
        Return all objects exactly at a given position.
        """

        return [ obj for obj in self.entities if obj.position == position ]

    def objects_near(self, position, radius):
        """
        Return all objects within radius of position.
        """

        radius2 = radius * radius
        return [ obj for obj in self.entities  
                if distance2(position, obj.position) <= radius2 ]

    def model_precept(self, precept, other):
        return precept


class EmitSound(object):
    """
    Class that manages how sounds are played and emitted from the area
    """

    def __init__(self, filename, ttl):
        self.filename = filename
        self.ttl = ttl
        self._done = 0
        self.timer = 0

    def update(self, time):
        if self.timer >= self.ttl:
            self._done = 1
        else:
            self.timer += time

    @property
    def done(self):
        return self._done


class PlatformMixin(object):
    """
    Mixin class is suitable for platformer games
    """

    def defaultPosition(self):
        return 0,0


    def translate(self, (x, y, z)):
        return y, z


    def worldToPixel(self, (x, y)):
        return (x, y)


    def worldToTile(self, (x, y, z)):
        xx = int(x) / self.tmxdata.tilewidth
        yy = int(y) / self.tmxdata.tileheight
        zz = 0
        return xx, yy, zz


"""
    G R O U P S


    1:  LEVEL GEOMETRY
    2:  ZONES



    T Y P E S

    1:  THE PLAYER (AS SET BY THE LEVEL STATE)
    2:  ZONES

"""

class PlatformArea(AbstractArea, PlatformMixin):
    """
    2D environment for things to live in.
    Includes basic pathfinding, collision detection, among other things.

    Physics simulation is handled by pymunk/chipmunk 2d physics.

    AI is supplimented by a pyGOAP environment.

    Expects to load a specially formatted TMX map created with Tiled.
    Layers:
        Control Tiles
        Upper Partial Tiles
        Lower Partial Tiles
        Lower Full Tiles

    The control layer is where objects and boundaries are placed.  It will not
    be rendered.  Your map must not have any spaces that are open.  Each space
    must have a tile in it.  Blank spaces will not be rendered properly and
    will leave annoying trails on the screen.

    The control layer must be created with the utility included with lib2d.  It
    contains metadata that lib2d can use to layout and position objects
    correctly.

    TODO: write some kind of saving!
    """

    gravity = (0, 150)


    def defaultSize(self):
        # TODO: this cannot be hardcoded!
        return (10, 8)


    def __init__(self):
        AbstractArea.__init__(self)
        self.subscribers = []

        self.exits    = {}
        self.tmxdata = None
        self.mappath = None
        self.soundmap = {}
        self.currentSounds = []

        # allow for entities to be added or removed during an update 
        self.inUpdate = False
        self._addQueue = []
        self._removeQueue = []

        self.geometry = {}

        # simple model of the game world for AI to use
        self.area_model = None


    def load(self):
        import pytmx

        self.tmxdata = pytmx.tmxloader.load_pygame(
                       self.mappath, force_colorkey=(128,128,0))

        # physics simulation
        self.space = pymunk.Space()
        self.space.damping = 0.9
        self.space.gravity = self.gravity

        # simple model of the game world for AI to use
        self.area_model = AreaEnvironment(self)

        # transform the saved geometry into chipmunk geometry and add it
        # bug: will not work with multiple layers
        geometry = []
        for layer, rects in self.geometry.items():
            for rect in rects:
                shape = pymunk.Poly(self.space.static_body, toChipPoly(rect))
                shape.friction = 2.0
                geometry.append(shape)

        self.space.add(geometry)

        # just assume we have the correct types under us
        for child in self._children:
            if child.avatar:
                if child.physics:
                    child.grounded = False
                    child.landing_previous = False
                    child.landing = {'p':pymunk.Vec2d.zero(), 'n':0}
                    self.space.add(*child.bodies)
                    self.space.add(*child.shapes)
                    self.space.add(*child.joints)

                # add this to the AI simulation
                agent = child.build_agent()
                if agent:
                    agent.parent = child
                    self.area_model.add(agent, child)
                else:
                    self.area_model.add(ObjectBase(child.name), child)

            elif isinstance(child, Zone):
                for s in child.shapes:
                    s.collision_type = 1
                self.space.add(child.shapes)

            else:
                self.space.add(*child.bodies)
                self.space.add(*child.shapes)
                self.space.add(*child.joints)



    def unload(self):
        # save the bodies here
        for child in self.children:
            if hasattr(child, "body"):
                child.position = body.position

        self.area_model = None
        self.space = None


    def add(self, child, pos=None):
        if self.inUpdate:
            self._addQueue.append(child)
            return

        AbstractArea.add(self, child)

        if child.avatar:
            if pos is None:
                pos = self.defaultPosition()
            else:
                pos = self.translate(pos)

            child.position = pos


    def remove(self, entity):
        if self.inUpdate:
            self._removeQueue.append(entity)
            return

        AbstractArea.remove(self, entity)
        del self.bodies[entity]


    def setLayerGeometry(self, layer, rects):
        """
        set the layer's geometry.  expects a list of rects.
        """

        self.geometry[layer] = rects


    def emitSound(self, filename, pos=None, entity=None, ttl=350):
        if pos==entity==None:
            raise ValueError, "emitSound requires a position or entity"

        #self.currentSounds = [ s for s in self.currentSounds if not s.done ]
        #if filename not in [ s.filename for s in self.currentSounds ]:
        if 1:
            self.currentSounds.append(EmitSound(filename, ttl))
            if entity:
                pos = entity.position
            for sub in self.subscribers:
                sub.emitSound(filename, pos)


    def update(self, time):
        self.inUpdate = True

        [ sound.update(time) for sound in self.sounds ]

        entities = ( c for c in self.children if hasattr(c, 'body') )
        for entity in entities:
            if not entity.avatar:
                continue

            body = entity.body

            grounding = {
                'normal' : pymunk.Vec2d.zero(),
                'penetration' : pymunk.Vec2d.zero(),
                'impulse' : pymunk.Vec2d.zero(),
                'position' : pymunk.Vec2d.zero(),
                'body' : None
            }
                   
            def f(arbiter):
                n = -arbiter.contacts[0].normal
                if n.y > grounding['normal'].y:
                    grounding['normal'] = n
                    grounding['penetration'] = -arbiter.contacts[0].distance
                    grounding['body'] = arbiter.shapes[1].body
                    grounding['impulse'] = arbiter.total_impulse
                    grounding['position'] = arbiter.contacts[0].position

                    entity.grounding = grounding

            body.each_arbiter(f)
            entity.avatar.update(time)

            # copy/paste from pymunk platformer, not sure if needed
            if grounding['body'] != None:
                friction = -(2.5/0.05)/self.space.gravity.y

                if abs(grounding['normal'].x/grounding['normal'].y) < friction:
                    entity.grounded = True
                else:
                    entity.grounded = False
            else:
                entity.grounded = False

            # check if falling body has landed
            if (abs(grounding['impulse'].y) / body.mass > 0) \
                and not entity.landed_previous:

                entity.landing = {'p':grounding['position'],'n':5}
                entity.landed_previous = True
                entity.grounded = True
            else:
                entity.landed_previous = False

            if entity.landing['n'] > 0:
                entity.landing['n'] -= 1

        self.space.step(time*2)
        self.area_model.update(time)

        # awkward looping allowing objects to be added/removed during update
        self.inUpdate = False
        [ self.add(entity) for entity in self._addQueue ] 
        [ self.remove(entity) for entity in self._removeQueue ] 
        self._addQueue = []
        self._removeQueue = []


    #  CLIENT API  --------------


    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber):
        self.subscribers.remove(subscriber)
