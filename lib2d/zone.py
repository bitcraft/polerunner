"""
Zones are a special construct that detects when objects are inside of them
"""

from objects import GameObject
from pygame import Rect
import pymunk



def toChipPoly(rect):
    return (rect.topleft, rect.topright, rect.bottomright, rect.bottomleft)


# expects to be given a PyTMX object node
class Zone(GameObject):
    def __init__(self, data):
        GameObject.__init__(self)
        self.rect = Rect(data.x, data.y, data.width, data.height)
        if hasattr(data, 'points'):
            self.points = data.points
        else:
            self.points = None
        self.name = data.name
        self.properties = data.properties
        self.entered = False

    def load(self):
        body = pymunk.Body(9999, pymunk.inf)
        self.body = body
        self.bodies = [body]
        self.shapes = [pymunk.Poly(body, toChipPoly(self.rect))]
