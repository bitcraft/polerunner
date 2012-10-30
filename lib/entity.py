from lib2d.objects import AvatarObject


class InteractiveObject(AvatarObject):
    """
    these objects supply a list of actions that other objects can call
    """

    physics = False

    def __init__(self, avatar, builders=None):
        AvatarObject.__init__(self, avatar)
        self.actionBuilders = builders


    def queryActions(self, caller):
        actions = []
        for builder in self.actionBuilders:
            actions.extend(builder.get_actions(caller, None))
        return actions


class Entity(InteractiveObject):
    """
    Game object that is capable of containing other objects and moving/being
    moved
    """

    physics = True
    move_speed = .001      # m/s
    jump_strength = .5  # for low gravity

    def __init__(self, avatar, builders, face, sounds=[]):
        super(Entity, self).__init__(avatar, builders)
        self.faceImage = face
        self.held = None
        self.grounded = False
        self.sounds = sounds
