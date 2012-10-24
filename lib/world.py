from lib2d.area import AbstractArea
from lib2d.avatar import Avatar
from lib2d.animation import Animation, StaticAnimation
from lib2d.objects import AvatarObject
from lib2d.image import Image, ImageTile
from lib2d import res
from lib.buildarea import fromTMX
from lib.level import Level
from lib.entity import Entity

from items import *
from enemies import *


def build():
    res.defaults.colorkey = True

    # build the initial environment
    uni = AbstractArea()
    uni.name = 'universe'
    uni.setGUID(0)

    # =========================================================================
    # our charming hero

    avatar = Avatar([
        Animation('idle',
            Image('hero-idle.png'),
            range(9), 1, 100),
        Animation('brake',
            Image('hero-brake.png'),
            range(6), 1, 30),
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
        Animation('jump',
            Image('hero-jump.png'),
            range(4), 1, 20),
        Animation('die',
            Image('hero-die.png'),
            range(3), 1, 85),
        StaticAnimation('falling',
            ImageTile('hero-die.png', (0,0), (32,32))),
        StaticAnimation('roll',
            Image('hero-roll.png')),
            #range(8), 1, 30),
        
    ])

    npc = Entity(
        avatar,
        [],
        Image('face0.png')
    )

    npc.setName("Brahbrah")
    npc.setGUID(1)
    npc.size = (16,12,32)
    npc.move_speed = 1   #.025
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

    red_key = Key(avatar)
    red_key.setName('Red Key')
    red_key.setGUID(513)
    uni.add(red_key)


    # green
    avatar = Avatar([
        StaticAnimation('stand',
            Image('green-key.png'))
    ])

    green_key = Key(avatar)
    green_key.setName('Green Key')
    green_key.setGUID(514)
    uni.add(green_key)


    # blue
    avatar = Avatar([
        StaticAnimation('stand',
            Image('blue-key.png'))
    ])

    blue_key = Key(avatar)
    blue_key.setName('Blue Key')
    blue_key.setGUID(515)
    uni.add(blue_key)


    # floating security bot
    # =========================================================================

    avatar = Avatar([
        StaticAnimation('fall',
            Image('bot0-idle-0001.png')),
        StaticAnimation('hover',
            Image('bot0-hover-0001.png')),
    ])

    npc = HoverBot(
        avatar,
        [],
        Image('face0.png')
    )

    npc.setName("bot0")
    npc.setGUID(516)
    npc.size = (16,16,16)
    npc.move_speed = .5   #.025
    npc.jump_strength = .5
    uni.add(npc)



    # =========================================================================
    # levels
    level = fromTMX(uni, "level2.tmx")
    level.setName("Level 1")
    level.setGUID(5001)

    #level = Area()
    #level.setGUID(5001)
    #uni.add(level)

    return uni
