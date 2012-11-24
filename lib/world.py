from lib2d.area import AbstractArea
from lib2d.avatar import Avatar
from lib2d.animation import Animation, StaticAnimation
from lib2d.image import Image, ImageTile
from lib2d.sound import Sound
from lib2d import res
from lib.buildarea import fromTMX
from lib.entity import Entity

from items import *
from enemies import *


def build():
    res.defaults.colorkey = True

    # build the initial environment
    # the name is not important, but the GUID should always be 0
    uni = AbstractArea(guid=0)
    uni.name = 'universe'

    # =========================================================================
    # our charming hero

    avatar = Avatar([
        Animation('idle',
            Image('hero-idle.png'),
            range(9), 1, 100),
        Animation('brake',
            Image('hero-brake.png'),
            range(6), 1, 30),
        Animation('unbrake',
            Image('hero-brake.png'),
            range(5,-1,-1), 1, 30),
        Animation('walk',
            Image('hero-walk.png'),
            range(10), 1, 70),
        Animation('crouch',
            Image('hero-crouch.png'),
            range(5), 1, 30),
        Animation('uncrouch',
            Image('hero-uncrouch.png'),
            range(5), 1, 30),
        Animation('run',
            Image('hero-run.png'),
            range(16), 1, 30),
        Animation('sprint',
            Image('hero-sprint.png'),
            range(17), 1, 20),
        Animation('wait',
            Image('hero-wait.png'),
            range(6), 1, 100),
        Animation('die',
            Image('hero-die.png'),
            range(3), 1, 85),
        StaticAnimation('jumping',
            ImageTile('hero-jump.png', (2,0), (32,32))),
        StaticAnimation('falling',
            ImageTile('hero-die.png', (0,0), (32,32))),
        StaticAnimation('roll',
            Image('hero-roll.png'))],
        axis_offset = (8,0)
    )

    npc = Entity(
        (   
            avatar,
            Sound('stop.wav'),
        ),
        guid=1
    )

    npc.setName("Brahbrah")
    npc.size = (16,32)
    npc.jump_strength = 400
    uni.add(npc)


    # =========================================================================
    # some keys

    # red
    #avatar = Avatar([
    #    StaticAnimation(
    #        Image('red-key.png', colorkey=True),
    #        'stand')
    #])

    avatar = Avatar([
        Animation('stand',
            Image('red-key-spinning.png'),
            range(12), 1, 100)
    ])

    red_key = Key(avatar, guid=513)
    red_key.setName('Red Key')
    uni.add(red_key)


    # green
    avatar = Avatar([
        StaticAnimation('stand',
            Image('green-key.png'))
    ])

    green_key = Key(avatar, guid=514)
    green_key.setName('Green Key')
    uni.add(green_key)


    # blue
    avatar = Avatar([
        StaticAnimation('stand',
            Image('blue-key.png'))
    ])

    blue_key = Key(avatar, guid=515)
    blue_key.setName('Blue Key')
    uni.add(blue_key)


    # =========================================================================

    # floating security bot
    # =========================================================================

    avatar = Avatar([
        StaticAnimation('fall',
            Image('bot0-idle-0001.png')),
        StaticAnimation('hover',
            Image('bot0-hover-0001.png')),
    ])

    npc = HoverBot((avatar, Sound('Hover0.wav')))

    npc.setName("bot0")
    npc.setGUID(516)
    npc.size = (16,32,16)
    npc.move_speed = .5   #.025
    npc.jump_strength = .5
    uni.add(npc)



    # =========================================================================
    # levels
    level = fromTMX(uni, "level4.tmx")
    level.setName("Level 1")
    level.setGUID(5001)

    #level = Area()
    #level.setGUID(5001)
    #uni.add(level)

    return uni
