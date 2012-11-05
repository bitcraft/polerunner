from renderer import LevelCamera

from lib2d.signals import *
from lib2d.playerinput import KeyboardPlayerInput
from lib2d import res, ui, gfx, context, sound

from lib2d.zone import Zone
from lib.controllers import HeroController
from lib.dialog import *

import pygame, math, time


"""
FUTURE:
    Create immutable types when possible to reduce headaches when threading
"""

debug = 1
movt_fix = 1/math.sqrt(2)


def getNearby(thing, d):
    p = thing.driver
    body = p.getBody(thing)
    bbox = body.bbox.inflate(64,d,d)
    x1, y1, z1 = body.bbox.center
    nearby = []
    for other in p.testCollideObjects(bbox, skip=[body]): 
        x2, y2, z2 = other.bbox.center
        dist = math.sqrt(pow(x1-x2, 2) + pow(y1-y2, 2) + pow(z1-z2, 2))
        nearby.append((d, (other.driver, other)))

    return [ i[1] for i in sorted(nearby) ]


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



class LevelState(context.Context):
    """
    This state is where the player will move the hero around the map
    interacting with npcs, other players, objects, etc.

    much of the work done here is in the Standard UI class.
    """

    def __init__(self, driver, area):
        super(LevelState, self).__init__(driver)
        self.area = area


    def enter(self):
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

        self.controllers = []

        keyboard = KeyboardPlayerInput()

        self.hero = self.area.getChildByGUID(1)
        self.hero_body = self.area.getBody(self.hero)

        # set so player doesn't collide with zones
        self.area.shapes[self.hero].collision_type = 1

        c1 = HeroController(self.hero)
        c1.program(keyboard)
        c1.primestack()

        self.driver.inputs.append(keyboard)
        self.controllers.append(c1)

        self.area.space.add_collision_handler(1,2, begin=self.overlap_zone)

        self.paused = False

        self.queued_state = None


    def overlap_zone(self, space, arbiter):
        for zone in [i for i in self.area._children if isinstance(i, Zone)]:
            if self.area.shapes[zone] is arbiter.shapes[1]:
                if not zone.entered:
                    self.enter_zone(zone)
                    zone.entered = True
                    break

        return False


    def enter_zone(self, zone):
        ctx = TextDialog(self.driver)
        ctx.prompt(zone.properties['TouchMessage'])
        self.queued_state = ctx

    def reenter(self):
        [ c.reset() for c in self.controllers ]
        pass

    def update(self, time):
        if not self.paused:
            self.area.update(time)
            [ c.update(time) for c in self.controllers ]

        if self.queued_state:
            self.driver.append(self.queued_state)
            self.queued_state = None
            return


    def draw(self, surface):
        self.camera.center(self.hero_body.position)
        self.ui.draw(surface)


    def handle_command(self, cmd):
        #self.ui.handle_commandlist(cmdlist)
        #self.handleMovementKeys(cmdlist)
        [ c.process(cmd) for c in self.controllers ]

            #if cmd == P1_ACTION1:
            #    for thing, body in getNearby(self.hero, 8):
            #        if hasattr(thing, "use"):
            #            thing.use(self.hero)

            #elif cmd == P1_ACTION3:
            #    for thing, body in getNearby(self.hero, 6):
            #        if thing.pushable and not self.hero.held:
            #            self.hero.driver.join(hero_body, body)
            #            self.hero.held = body
            #            msg = self.text['grab'].format(thing.name) 
            #            self.hero.driver.emitText(msg, thing=self.hero)


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
