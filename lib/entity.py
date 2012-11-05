from lib2d.objects import GameObject

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

