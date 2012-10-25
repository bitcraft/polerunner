from renderer import LevelCamera

from lib2d.buttons import *
from lib2d.signals import *
from lib2d.playerinput import KeyboardPlayerInput, MousePlayerInput
from lib2d import res, ui, gfx, context

from lib.controllers import HeroController

import pygame, math, time


"""
FUTURE:
    Create immutable types when possible to reduce headaches when threading
"""

debug = 1
movt_fix = 1/math.sqrt(2)


def getNearby(thing, d):
    p = thing.parent
    body = p.getBody(thing)
    bbox = body.bbox.inflate(64,d,d)
    x1, y1, z1 = body.bbox.center
    nearby = []
    for other in p.testCollideObjects(bbox, skip=[body]): 
        x2, y2, z2 = other.bbox.center
        dist = math.sqrt(pow(x1-x2, 2) + pow(y1-y2, 2) + pow(z1-z2, 2))
        nearby.append((d, (other.parent, other)))

    return [ i[1] for i in sorted(nearby) ]


class SoundManager(object):
    def __init__(self):
        self.sounds = {}
        self.last_played = {}

    def loadSound(self, filename):
        self.sounds[filename] = res.loadSound(filename)
        self.last_played[filename] = 0

    def play(self, filename, volume=1.0):
        now = time.time()
        if self.last_played[filename] + .05 <= now:
            self.last_played[filename] = now
            sound = self.sounds[filename]
            sound.set_volume(volume)
            sound.play()

    def unload(self):
        self.sounds = {}
        self.last_played = {}


SoundMan = SoundManager()



class LevelUI(ui.UserInterface):
    pass



class LevelState(context.Context):
    """
    This state is where the player will move the hero around the map
    interacting with npcs, other players, objects, etc.

    much of the work done here is in the Standard UI class.
    """

    def __init__(self, parent, area):
        super(LevelState, self).__init__(parent)
        self.area = area
        self.hero = area.getChildByGUID(1)
        self.hero_body = self.area.getBody(self.hero)

        # awkward input handling
        self.player_vector = [0,0,0]
        self.wants_to_stop_on_landing = False
        self.input_changed = False
        self.jumps = 0


    def activate(self):
        self.ui = LevelUI()
        vpm = ui.Frame(self.ui, ui.GridPacker())
        vp = ui.ViewPort(self.ui, self.area)
        vpm.addElement(vp)
        self.ui.addElement(vpm)
        self.ui.rect = gfx.get_rect()

        self.camera = vp.camera

        for filename in self.area.soundFiles:
            SoundMan.loadSound(filename)

        # hackish pub/sub
        self.area.subscribe(self)

        self.controllers = []

        keyboard = KeyboardPlayerInput()

        c1 = HeroController(self.hero)
        c1.setup(keyboard)

        self.parent.inputs.append(keyboard)
        self.controllers.append(c1)


    def update(self, time):
        self.area.update(time)
        [ c.update(time) for c in self.controllers ]


    def draw(self, surface):
        self.camera.center(self.hero_body.position)
        self.ui.draw(surface)


    def handle_commandlist(self, cmdlist):
        #self.ui.handle_commandlist(cmdlist)
        #self.handleMovementKeys(cmdlist)

        for cmd in cmdlist:
            [ c.process(cmd) for c in self.controllers ]

            #if cmd == P1_ACTION1:
            #    for thing, body in getNearby(self.hero, 8):
            #        if hasattr(thing, "use"):
            #            thing.use(self.hero)

            #elif cmd == P1_ACTION3:
            #    for thing, body in getNearby(self.hero, 6):
            #        if thing.pushable and not self.hero.held:
            #            self.hero.parent.join(hero_body, body)
            #            self.hero.held = body
            #            msg = self.text['grab'].format(thing.name) 
            #            self.hero.parent.emitText(msg, thing=self.hero)


    def emitSound(self, filename, position):
        x1, y1 = position
        x2, y2 = self.hero_body.position
        d = math.sqrt(pow(x1-x2, 2) + pow(y1-y2, 2))
        try:
            vol = 1/d * 20 
        except ZeroDivisionError:
            vol = 1.0
        if vol > .02:
            SoundMan.play(filename, volume=vol)
