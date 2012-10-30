from entity import InteractiveObject
from lib2d.avatar import Avatar
from lib2d.animation import StaticAnimation
from lib2d.image import Image


avatar = Avatar([
    StaticAnimation('idle', Image('guide.png'))
])


class Guide(InteractiveObject):
    def __init__(self, guid, text):
        InteractiveObject.__init__(self, avatar)
        self.setGUID(guid)
        self.setName(text[:12])
        self.text = text
        self.size = (16,16,16)
