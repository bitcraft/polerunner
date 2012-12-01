from renderer import LevelCamera

from lib.controllers import HeroController
from lib.dialog import *
from lib2d.zone import Zone
from lib2d import res, ui, gfx, context, sound, game

import pygame, math, time



class SoundManager(object):
    def __init__(self):
        self.sound_map = {}
        self.last_played = {}

    def loadSound(self, sound):
        self.sound_map[sound.filename] = sound
        self.last_played[sound.filename] = 0

    def play(self, filename, volume=1.0):
        sound = self.sound_map[filename]
        sound.volume = volume
        sound.play()

    def unload(self):
        self.sound_map = {}
        self.last_played = {}


SoundMan = SoundManager()

class LevelUI(ui.UserInterface):
    pass

class LevelState(game.GameContext):
    """
    This state is where the player will move the hero around the map
    interacting with npcs, other players, objects, etc.
    """

    def __init__(self, area):
        self.area = area


    def enter(self):
        self.area.loadAll()
    
        self.controllers = []

        self.ui = LevelUI()
        vpm = ui.Frame(self.ui, ui.GridPacker())
        vp = ui.ViewPort(self.ui, self.area)
        vpm.addElement(vp)
        self.ui.addElement(vpm)
        self.ui.rect = gfx.get_rect()

        self.camera = vp.camera

        [ SoundMan.loadSound(c) for c in self.area.getChildren()
          if isinstance(c, sound.Sound) ]

        # hackish pub/sub
        self.area.subscribe(self)

        self.hero = self.area.getChildByGUID(1)

        c1 = HeroController(self.hero)
        c1.program(self.parent.inputs[0])
        c1.primestack()

        self.controllers.append(c1)
        self.area.space.add_collision_handler(0,1, begin=self.overlap_zone)
        self.paused = False


    def exit(self):
        self.ui = None
        self.camera = None
        # unload sounds

        self.area.unsubscribe(self)

        self.hero = None

        [ c.reset() for c in self.controllers ]
        self.controllers = []


    def overlap_zone(self, space, arbiter):
        ok = False
        for shape in self.hero.shapes:
            if shape in arbiter.shapes:
                ok = True
                break

        if not ok:
            return False

        for zone in [i for i in self.area if isinstance(i, Zone)]:
            if zone.shapes[0] is arbiter.shapes[1]:
                if not zone.entered:
                    self.enter_zone(zone)
                    zone.entered = True
                    break

        return False


    def enter_zone(self, zone):
        if zone.properties.has_key('TouchMessage'):
            self.parent.append(TextDialog(zone.properties['TouchMessage']))


    def update(self, time):
        if not self.paused:
            self.area.update(time)
            [ c.update(time) for c in self.controllers ]


    def draw(self, surface):
        self.camera.center(self.hero.body.position)
        self.ui.draw(surface)


    def handle_command(self, cmd):
        [ c.process(cmd) for c in self.controllers ]


    def emitSound(self, filename, position):
        x1, y1 = position
        x2, y2 = self.hero.body.position
        d = math.sqrt(pow(x1-x2, 2) + pow(y1-y2, 2))
        try:
            vol = 1/d * 20 
        except ZeroDivisionError:
            vol = 1.0
        if vol > .02:
            SoundMan.play(filename, volume=vol)
