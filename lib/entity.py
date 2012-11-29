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

    def init(self):
        pass

    def update(self, time):
        pass

    def build_agent(self):
        return None

    def build_body(self):
        """
        should return the body as arg 0 and any shapes as remaining arguments
        """

        r = self.size[0]/ 2
        m = pymunk.moment_for_circle(self.mass, r, r)

        self.body = pymunk.Body(self.mass, pymunk.inf)
        #self.body = pymunk.Body(self.mass, m)
        return self.body

    def build_shapes(self, body):
        self.body_shape = pymunk.Poly.create_box(body, size=self.size[:2])
        self.body_shape.friction = 1.0
        self.feet = pymunk.Circle(body, self.size[0] / 2, (0, 8))
        self.feet.friction = 1.0

        return [self.body_shape]
