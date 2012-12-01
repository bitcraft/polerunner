from lib2d.objects import InteractiveObject
from lib2d.avatar import Avatar
from lib2d.animation import StaticAnimation
from lib2d.image import Image
from pygame import Rect
import pymunk



class Key(InteractiveObject):
    pass


class FreeWheel(InteractiveObject):
    physics = True
    mass = 100

    acceptableChildren = [Avatar]

    def __init__(self, data):
        InteractiveObject.__init__(self)
        self.rect = Rect(data.x, data.y, data.width, data.height)
        self.radius = self.rect.width / 2
        self.rect.y -= 3
        if hasattr(data, 'points'):
            self.points = data.points
        else:
            self.points = None
        self.name = data.name

    @property
    def body(self):
        return self.bodies[0]

    def load(self):
        m = pymunk.moment_for_circle(self.mass, 0, self.radius)

        base = pymunk.Body()
        base.position = self.rect.center

        body = pymunk.Body(self.mass, m)
        body.position = self.rect.center
        body_shape = pymunk.Circle(body, self.radius)
        body_shape.friction = 1.0
        body_shape.collision_type = 2

        joint = pymunk.PinJoint(base, body, (0,0), (0,0))
        #motor = pymunk.SimpleMotor(body, feet, 0.0)

        self.bodies = [body]
        self.shapes = [body_shape]
        self.joints = [joint]

        size = (self.radius*2, self.radius*2)

        self.add(Avatar([
            StaticAnimation('idle', Image('wheel.png', alpha=1, resize=size))
        ]))

        self._avatar = None
        self._loaded = True

    def build_agent(self):
        return None
