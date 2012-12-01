from lib2d.objects import GameObject
import pymunk



class InteractiveObject(GameObject):
    """
    these objects supply a list of actions that other objects can call
    """

    def __init__(self, avatar, builders=None, **kwargs):
        GameObject.__init__(self, avatar, **kwargs)
        self.actionBuilders = builders


    def queryActions(self, caller):
        actions = []
        for builder in self.actionBuilders:
            actions.extend(builder.get_actions(caller, None))
        return actions


class Entity(InteractiveObject):
    """
    GameObject that is interactive.
    Is capable of receiving events.
    """

    physics = True
    mass = 5
    size = (16, 16, 16)

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

    def load(self):
        r = self.size[0]/ 2
        w = self.size[0]
        h = self.size[1] - r * 2
        m = pymunk.moment_for_circle(self.mass, r, r)

        body = pymunk.Body(self.mass, pymunk.inf)
        body.position = self._position
        body_shape = pymunk.Poly.create_box(body, size=(w, h))
        body_shape.friction = 1.0
        body_shape.collision_type = 1

        feet = pymunk.Body(1, m)
        feet.position = self._position + (0, r*2)
        feet_shape = pymunk.Circle(feet, r)
        feet_shape.friction = 1.0
        feet_shape.collision_type = 2

        joint = pymunk.PinJoint(body, feet, (0, r*2), (0,0))
        motor = pymunk.SimpleMotor(body, feet, 0.0)

        self.bodies = [body, feet]
        self.shapes = [body_shape, feet_shape]
        self.joints = [joint, motor]
        self._loaded = True

    def unload(self):
        self._position = pymunk.Vec2d(self.body.position)
        self.bodies = []
        self.shapes = []
        self._loaded = False
