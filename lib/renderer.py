from lib2d.tilemap import BufferedTilemapRenderer
from lib2d.objects import GameObject
from lib2d.ui import Element

from pygame import Rect, draw, Surface
from pygame.transform import rotozoom

from pymunk.pygame_util import draw_space, from_pygame, to_pygame
import pymunk
import math


DEBUG = 1

parallax = 0


def screenSorter(a):
    return a[-1].x

def toBB(rect):
    return pymunk.BB(rect.left, rect.top, rect.right, rect.bottom)

class LevelCamera(Element):
    """
    The level camera manages sprites on the screen and a tilemap renderer.
    """

    name = 'LevelCamera'

    def __init__(self, parent, area, extent):
        Element.__init__(self, parent)

        self.area = area
        self.set_extent(extent)

        w, h = self.extent.size

        # create a renderer for the map
        self.maprender = BufferedTilemapRenderer(area.tmxdata, (w, h))
        self.map_width = area.tmxdata.tilewidth * area.tmxdata.width
        self.map_height = area.tmxdata.tileheight * area.tmxdata.height
        self.blank = True

        if parallax:
            import pytmx, lib2d.res

            # EPIC HACK GO
            i = lib2d.res.loadImage("../tilesets/level0.png")
            colorkey = i.get_at((0,0))[:3]
            self.maprender.buffer.set_colorkey(colorkey)
            #self.maprender.buffer = self.maprender.buffer.convert_alpha()
            par_tmx = pytmx.tmxloader.load_pygame(
            lib2d.res.mapPath('parallax4.tmx'), force_colorkey=(128,128,0))
            self.parallaxrender = BufferedTilemapRenderer(par_tmx, (w, h))
 

    def set_extent(self, extent):
        """
        the camera caches some values related to the extent, so it becomes
        necessary to call this instead of setting the extent directly.
        """

        self.extent = Rect(extent)

        self.half_width = self.extent.width / 2
        self.half_height = self.extent.height / 2
        self.width  = self.extent.width
        self.height = self.extent.height
        self.zoom = 1.0


    def center(self, (x, y)):
        """
        center the camera on a world location.
        """

        if self.map_height >= self.height:
            if y <= self.half_height:
                y = self.half_height

            elif y > self.map_height - self.half_height- 1:
                y = self.map_height - self.half_height - 1 
        else:
            y = self.map_height / 2

        if self.map_width >= self.width:
            if x <= self.half_width:
                x = self.half_width

            elif x > self.map_width - self.half_width - 1:
                x = self.map_width - self.half_width - 1

        else:
            x = self.map_width / 2

        self.extent.center = (x, y)
        self.maprender.center((x, y))

        if parallax:
            self.parallaxrender.center((x/2.0, y/2.0))


    def clear(self, surface):
        raise NotImplementedError


    def draw(self, surface, rect):
        onScreen = []

        if self.blank:
            self.blank = False
            self.maprender.blank = True

        visible_shapes = self.area.space.bb_query(toBB(self.extent))

        for child in [ child for child in self.area if child.avatar]:
            shape = child.shapes[0]
            if shape not in visible_shapes:
                continue

            bb = child.bb
            x = bb.left - self.extent.left - child.avatar.axis.x
            y = bb.top - self.extent.top

            if hasattr(shape, "radius"):
                w, h = child.avatar.image.get_size()
                angle = -(math.degrees(shape.body.angle)) % 360
                image = rotozoom(child.avatar.image.convert_alpha(), angle, 1.0)
                ww, hh = image.get_size()
                rrect = Rect(x, y-h, ww, hh)
                rrect.move_ip((w-ww)/2, (h-hh)/2)
            else:
                w, h = child.avatar.image.get_size()
                rrect = Rect(x, y - h, w, h)
                image = child.avatar.image
            onScreen.append((image, rrect, 1))

        if parallax:
            self.parallaxrender.draw(surface, rect, [])

        dirty = self.maprender.draw(surface, rect, onScreen)

        if DEBUG:
            def translate((x, y)):
                return x - self.extent.left, y - self.extent.top

            for shape in self.area.space.shapes:
                try:
                    points = [ translate(i) for i in shape.get_points() ]
                except AttributeError:
                    pass
                else:
                    draw.aalines(surface, (255,100,100), 1, points)
                    continue

                try:
                    radius = shape.radius
                    pos = shape.body.position
                    pos = translate(pos)
                    pos += shape.offset
                except AttributeError:
                    pass
                else:
                    pos = map(int, pos)
                    draw.circle(surface, (255,100,100), pos, int(radius), 1)
                    continue

        return dirty


    def worldToSurface(self, (x, y)):
        xx, yy = self.area.worldToPixel((x, y))
        return xx - self.extent.left, yy - self.extent.top


    def surfaceToWorld(self, (x, y)):
        """
        Transform surface coordinates to coordinates in the world
        surface coordinates take into account the camera's extent
        """

        return self.area.pixelToWorld((x+self.extent.top,y+self.extent.left))
