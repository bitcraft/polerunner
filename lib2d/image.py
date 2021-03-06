from lib2d import GameObject
from lib2d import res
import pygame


"""
lazy image loading
"""

def get_defaults():
    return res.defaults.__dict__.copy()


class Image(GameObject):
    """
    Surface class that is pickable.  :)
    """

    def __init__(self, filename, *args, **kwargs):
        GameObject.__init__(self)

        self.filename = filename
        self.args = args
        self.kwargs = get_defaults()
        self.kwargs.update(kwargs)
        self.image = None

    def load(self):
        self.image = res.loadImage(self.filename, *self.args, **self.kwargs)
        return self.image


class ImageTile(GameObject):
    """
    Allows you to easily pull tiles from other images
    """

    def __init__(self, filename, tile, tilesize):
        GameObject.__init__(self)

        self._image = Image(filename)
        self.add(self._image)
        self.tile = tile
        self.tilesize = tilesize

    def load(self):
        surface = self._image.image
        temp = pygame.Surface(self.tilesize).convert(surface)
        temp.blit(surface, (0,0),
                  ((self.tilesize[0] * self.tile[0],
                    self.tilesize[1] * self.tile[1]),
                    self.tilesize))
        if self._image.kwargs['colorkey']:
            temp.set_colorkey(temp.get_at((0,0)), pygame.RLEACCEL)

        self.image = temp
        return self.image
