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

        return pymunk.Body(self.mass, pymunk.inf)

    def build_shapes(self, body):
        shape = pymunk.Poly.create_box(body, size=self.size[:2])
        shape.friction = 1.0

        return [shape]
