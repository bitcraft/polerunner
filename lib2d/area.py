import res
from pathfinding.astar import Node
from objects import GameObject
from pygame import Rect
from pathfinding import astar
from lib2d.signals import *
from lib2d.zone import Zone
from lib2d.sound import Sound
import math

import pymunk

cardinalDirs = {"north": math.pi*1.5,
                "east": 0.0,
                "south": math.pi/2,
                "west": math.pi}


class AbstractArea(GameObject):
    pass


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
        return (x*self.scaling, y*self.scaling)


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

    REWRITE: FUNCTIONS HERE SHOULD NOT CHANGE STATE

    NOTE: some of the code is specific for maps from the tmxloader
    """

    gravity = (0, 50)


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
        self._addQueue = []

        # temporary storage of physics stuff
        self.saved_positions = {}

        # internal physics stuff
        self.geometry = {}
        self.shapes = {}
        self.bodies = {}
        self.scaling = 1.0


    def load(self):
        def toChipPoly(rect):
            return (rect.topleft, rect.topright,
                    rect.bottomright, rect.bottomleft)


        import pytmx

        self.tmxdata = pytmx.tmxloader.load_pygame(
                       self.mappath, force_colorkey=(128,128,0))

        self.space = pymunk.Space()
        self.space.gravity = self.gravity

        # transform the saved geometry into chipmunk geometry and add it
        # bug: will not work with multiple layers
        geometry = []
        for layer, rects in self.geometry.items():
            for rect in rects:
                shape = pymunk.Poly(self.space.static_body, toChipPoly(rect))
                shape.friction = 2.0
                shape.group = 1
                geometry.append(shape)

        self.space.add(geometry)

        # just assume we have the correct types under us
        for child in self._children:
            if child.avatar:
                if child.physics:
                    body = pymunk.Body(5, pymunk.inf)
                    body.position = self.saved_positions[child]
                    shape = pymunk.Poly.create_box(body, size=child.size[:2])
                    shape.friction = 1.0
                    self.bodies[child] = body
                    self.shapes[child] = shape
                    self.space.add(body, shape)

                else:
                    rect = Rect(self.saved_positions[child], child.size[:2])
                    shape = pymunk.Poly(self.space.static_body, toChipPoly(rect))
                    shape.friction = 0.5
                    self.shapes[child] = shape
                    self.space.add(shape)

            elif isinstance(child, Zone):
                points = toChipPoly(child.extent)
                shape = pymunk.Poly(self.space.static_body, points)
                shape.collision_type = 2
                self.shapes[child] = shape
                self.space.add(shape)


    def unload(self):
        # save the bodies here
        for entity, body in self.bodies.items():
            self.saved_positions[entity] = body.position

        self.bodies = {}
        self.shapes = {}
        self.physicsgroup = None
        self.space = None


    def add(self, child, pos=None):
        AbstractArea.add(self, child)

        # don't do anything with the physics engine here
        # handle it in load(), where the area is prepped for use

        if child.avatar:
            if pos is None:
                pos = self.defaultPosition()
            else:
                pos = self.translate(pos)

            self.saved_positions[child] = pos


    def remove(self, entity):
        if self.inUpdate:
            self._removeQueue.append(entity)
            return

        AbstractArea.remove(self, entity)
        del self.bodies[entity]


    def getBody(self, entity):
        return self.bodies[entity]


    def setLayerGeometry(self, layer, rects):
        """
        set the layer's geometry.  expects a list of rects.
        """

        self.geometry[layer] = rects


    def pathfind(self, start, destination):
        """Pathfinding for the world.  Destinations are 'snapped' to tiles.
        """

        def NodeFactory(pos):
            x, y = pos[:2]
            l = 0
            return Node((x, y))

            try:
                if self.tmxdata.getTileGID(x, y, l) == 0:
                    node = Node((x, y))
                else:
                    return None
            except:
                return None
            else:
                return node

        start = self.worldToTile(start)
        destination = self.worldToTile(destination)
        path = astar.search(start, destination, NodeFactory)
        return path


    def emitSound(self, filename, pos=None, entity=None, ttl=350):
        if pos==entity==None:
            raise ValueError, "emitSound requires a position or entity"

        self.currentSounds = [ s for s in self.currentSounds if not s.done ]
        if filename not in [ s.filename for s in self.currentSounds ]:
            self.currentSounds.append(EmitSound(filename, ttl))
            if entity:
                pos = self.bodies[entity].position
            for sub in self.subscribers:
                sub.emitSound(filename, pos)


    def update(self, time):
        self.inUpdate = True

        [ sound.update(time) for sound in self.sounds ]

        for entity, body in self.bodies.items():
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
            body.each_arbiter(f)
            entity.avatar.update(time)

            if grounding['body'] != None:
                friction = -(body.velocity.y/0.05)/self.space.gravity.y

            if grounding['body'] != None and abs(grounding['normal'].x/grounding['normal'].y) < friction:
                entity.grounded = True
            else:
                entity.grounded = False

            #entity.update(time)

        self.space.step(1.0/60)

        # awkward looping allowing objects to be added/removed during update
        self.inUpdate = False
        [ self.add(entity) for entity in self._addQueue ] 
        self._addQueue = []
        [ self.remove(entity) for entity in self._removeQueue ] 
        self._removeQueue = []


    #  CLIENT API  --------------


    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber):
        self.subscribers.remove(subscriber)
