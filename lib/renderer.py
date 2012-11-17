from lib2d.tilemap import BufferedTilemapRenderer
from lib2d.objects import GameObject
from lib2d.ui import Element

from pygame import Rect, draw, Surface

from pymunk.pygame_util import draw_space, from_pygame, to_pygame
import pymunk


DEBUG = 0

parallax = 1


def screenSorter(a):
    return a[-1].x


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

        x, y = self.area.worldToPixel((x, y))

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

        # TODO: query chipmunk to find visible objects
        for entity, shape in self.area.shapes.items():
            if entity.avatar:
                w, h = entity.avatar.image.get_size()
                try:
                    points = shape.get_points()
                except AttributeError:
                    temp_rect = entity.avatar.image.get_rect()
                    temp_rect.center = shape.body.position
                    x, y = self.area.worldToPixel(temp_rect.topleft)
                else:
                    l = 99999
                    t = 99999
                    r = 0
                    b = 0
                    for x, y in points:
                        if x < l: l = x
                        if x > r: r = x
                        if y < t: t = y
                        if y > b: b = y
                    ax, ay = entity.avatar.axis
                    x, y = self.area.worldToPixel((l-ax,b-ay))

                x -= self.extent.left
                y -= self.extent.top
                onScreen.append((entity.avatar.image, Rect((x, y), (w, h)), 1))

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
                    pos = translate((int(pos.x), int(pos.y)))
                except AttributeError:
                    pass
                else:
                    draw.circle(surface, (255,100,100), pos, int(radius), 1)
                    continue

        return dirty


    def worldToSurface(self, (x, y, z)):
        """
        Translate world coordinates to coordinates on the surface
        underlying area is based on 'right handed' 3d coordinate system
        xy is horizontal plane, with x pointing toward observer
        z is the vertical plane
        """

        xx, yy = self.area.worldToPixel((x, y, z))
        return xx - self.extent.left, yy - self.extent.top


    def surfaceToWorld(self, (x, y)):
        """
        Transform surface coordinates to coordinates in the world
        surface coordinates take into account the camera's extent
        """

        return self.area.pixelToWorld((x+self.extent.top,y+self.extent.left))
