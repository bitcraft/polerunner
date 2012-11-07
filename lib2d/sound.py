from lib2d import res, GameObject
import pygame
import functools


class Listener(object):
    """
    Singleton object that allows for volume changes for sounds based on their
    position in space
    """

    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Listener, cls).__new__(
                                  cls, *args, **kwargs)
        return cls._instance


    def __init__(self):
        self._position = None
        self._volume = 1.0


    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, (x, y)):
        self._position = (x, y)


    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value


listener = Listener()



def get_defaults():
    return res.defaults.__dict__.copy()


class Sound(GameObject):
    """
    Sound class that is pickable.  :)
    """

    def __init__(self, filename, *args, **kwargs):
        GameObject.__init__(self, **kwargs)

        self.sound = None
        self.filename = filename
        #self.args = args
        #self.kwargs = get_defaults()
        #self.kwargs.update(kwargs)

    def load(self):
        self.sound = res.loadSound(self.filename)

    def play(self, *args, **kwargs):
        if not self.sound: raise Exception
        self.sound.play(*args, **kwargs)

    def stop(self):
        if not self.sound: raise Exception
        self.sound.stop()

    def fadeout(self, time):
        if not self.sound: raise Exception
        self.sound.fadeout(time)

    @property
    def volume(self):
        if not self.sound: raise Exception
        return self.sound.get_volume()

    @volume.setter
    def volume(self, value):
        if not self.sound: raise Exception
        self.sound.set_volume(value)

