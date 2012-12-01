from lib2d.objects import GameObject
import pymunk



class InteractiveObject(GameObject):
    """
    these objects supply a list of actions that other objects can call
    """

    def __init__(self, avatar, builders=None, **kwargs):
        GameObject.__init__(self, avatar, **kwargs)
        self.actionBuilders = builders


    def queryActions(self, parent):
        actions = []
        for builder in self.actionBuilders:
            actions.extend(builder.get_actions(parent, None))
        return actions


class Entity(InteractiveObject):
    """
    Class for interactive and dynamic objects in the game.
    Entities are managed by the physics engine.
    """

    physics = True
    mass = 5
    size = (16, 16, 16)
    max_speed = 30

    def __init__(self, *args, **kwargs):
        InteractiveObject.__init__(self, *args, **kwargs)
        self.init()
        self.shapes = []
        self.bodies = []
        self.joints = []
        self._position = pymunk.Vec2d(0,0)
        self._loaded = False

    def init(self):
        pass

    def update(self, time):
        pass

    def build_agent(self):
        return None

    @property
    def position(self):
        if self._loaded:
            return self.body.position
        else:
            return self._position

    @position.setter
    def position(self, pos):
        self._position = pymunk.Vec2d(pos)
        if self._loaded:
            self.bodies[0].position = self._position

    @property
    def body(self):
        return self.bodies[0]

    @property
    def feet(self):
        return self.bodies[1]

    @property
    def motor(self):
        return self.joints[1]

    @property
    def bb(self):
        if len(self.shapes) == 1:
            return self.shapes[0].bb

        elif len(self.shapes) > 1:
            bb = self.shapes[0].bb
            for shape in self.shapes[1:]:
                bb = bb.merge(shape.bb)
            return bb


    def load(self):
        self.build_bodies()
        self.build_shapes()
        self._loaded = True


    def build_bodies(self):
        r = self.size[0] * 0.45
        w = self.size[0]
        h = self.size[1] - r * 2.5
        dx = w - r * 2
        m = pymunk.moment_for_circle(self.mass, 0, r)

        # force the entity to cache the current position
        if self.bodies:
            self._position = self.bodies[0].position

        body = pymunk.Body(self.mass - 1, pymunk.inf)
        body.position = self._position

        feet = pymunk.Body(1, m)
        feet.position = self._position + (dx, r*2.5)

        joint = pymunk.PivotJoint(body, feet, (0, r*2.5), (0,0))
        motor = pymunk.SimpleMotor(body, feet, 0.0)

        self.bodies = [body, feet]
        self.joints = [joint, motor]


    def build_shapes(self):
        r = self.size[0] * 0.45
        w = self.size[0]
        h = self.size[1] - r * 2

        body_shape = pymunk.Poly.create_box(self.body, size=(w, h))
        body_shape.friction = 1.0
        body_shape.collision_type = 1

        feet_shape = pymunk.Circle(self.feet, r)
        feet_shape.friction = 1.0
        feet_shape.collision_type = 2

        self.shapes = [body_shape, feet_shape]


    def rebuild(self):
        self.parent.space.remove(self.bodies, self.shapes, self.joints)
        self.build_bodies()
        self.build_shapes()
        self.parent.space.add(self.bodies, self.shapes, self.joints)


    def unload(self):
        self._position = pymunk.Vec2d(self.body.position)
        #self.parent.space.remove(self.bodies, self.shapes, self.joints)
        self.bodies = []
        self.shapes = []
        self.joints = []
        self._loaded = False
