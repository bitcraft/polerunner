from pytmx import tmxloader, buildDistributionRects
from lib2d.area import PlatformArea
from lib2d.zone import Zone
from lib2d.sound import Sound
from lib2d import res
from pygame import Rect
from lib.items import *


def debug(text):
    print "buildarea: {}".format(text)


def fromTMX(parent, mapname):
    """
    This function accepts a GameObject node and reorganizes it according to a
    TMX map.

    This means that the node passed must have all the objects that are
    referenced by the TMX map
    """

    # for platformer maps
    def toWorld(data, (x, y, z)):
        """ translate tiled map coordinates to world coordinates """
        return z, x*data.tilewidth, (y-1)*data.tileheight

    # for zelda-style games
    #def toWorld(data, (x, y, l)):
    #    """ translate tiled map coordinates to world coordinates """
    #    return y*data.tileheight, x*data.tilewidth, l


    area = PlatformArea()
    parent.add(area)
    area.parent = parent
    area.mappath = res.mapPath(mapname)
    data = tmxloader.load_tmx(area.mappath)

    # get sounds from tiles
    for i, layer in enumerate(data.tilelayers):
        props = data.getTilePropertiesByLayer(i)
        for gid, tileProp in props:
            for key, value in tileProp.items():
                if key[4:].lower() == "sound":
                    area.add(Sound(value))


    for gid, prop in data.tile_properties.items():
        try:
            prop['guid'] = int(prop['guid'])
        except KeyError:
            pass

    props = data.getTilePropertiesByLayer(-1)

    """
    print "GID MAP:"
    for k in sorted(data.gidmap.keys()):
        print "  {}: {}\t{}".format(k,
                                    data.gidmap[k],
                                    data.getTilePropertiesByGID(data.gidmap[k]))
    """

    # load the level geometry from the 'control' layer 
    rects = []
    for rect in buildDistributionRects(data, "Control", real_gid=1):
        rects.append(Rect(rect))

    area.setLayerGeometry(0, rects)
    area.tileheight = data.tileheight
    area.tilewidth = data.tilewidth

    # load the npc's and place them in the default positions 
    npcs = [ p for p in props if p[1].get('group', None) == 'npc' ] 

    for (gid, prop) in npcs:
        pos = data.getTileLocation(gid)
        if len(pos) > 1:
            msg = "control gid: {} is used in more than one locaton"
            raise Exception, msg.format(gid)

        x, y, z = toWorld(data, pos.pop())
        thing = area._parent.getChildByGUID(int(prop['guid']))
        debug("adding thing {} at {}".format(thing, (x, y, z)))
        area.add(thing, (x, y, z))
        #area.setOrientation(thing, "south")


    # load the items and place them where they should go
    # items can have duplicate entries
    items = [ p for p in props if p[1].get('group', None) == 'item' ]
    done = [] 

    for (gid, prop) in items:
        if gid in done: continue
        done.append(gid)

        locations = data.getTileLocation(gid)
        body = area._parent.getChildByGUID(int(prop['guid']))
        copy = False

        for pos in locations:
            # bodies cannot exists in multiple locations, so a copy is
            # made for each
            if copy:
                body = body.copy()

            x, y, z = toWorld(data, pos)

            area.add(body, (x, y, z))
            copy = True 

    # load the enemies and place them where they should go
    # enemies can have duplicate entries
    enemies = [ p for p in props if p[1].get('group', None) == 'enemy' ]
    done = [] 

    for (gid, prop) in enemies:
        if gid in done: continue
        done.append(gid)

        locations = data.getTileLocation(gid)
        body = area._parent.getChildByGUID(int(prop['guid']))
        copy = False

        for pos in locations:
            # bodies cannot exists in multiple locations, so a copy is
            # made for each
            if copy:
                body = body.copy()

            x, y, z = toWorld(data, pos)

            area.add(body, (x, y, z))
            copy = True 


    # level guides
    guides = [ p for p in props if p[1].get('group', None) == 'guide' ] 

    for (gid, prop) in guides:
        pos = data.getTileLocation(gid)
        if len(pos) > 1:
            msg = "control gid: {} is used in more than one locaton"
            raise Exception, msg.format(gid)

        x, y, z = toWorld(data, pos.pop())
        thing = area._parent.getChildByGUID(int(prop['guid']))
        debug("adding guide {} at {}".format(thing, (x, y, z)))
        area.add(thing, (x, y, z))


    # Zones
    # Zones should be configured in Tiled
    for og in data.objectgroups:
        if og.name.lower() == 'zones':
            for zone in og:
                area.add(Zone(zone))

        elif og.name.lower() == 'objects':
            for obj in og:
                if obj.name.lower() == 'wheel':
                    area.add(FreeWheel(obj))


    # handle the exits
    # here only the exits and positions are saved
    # another class will have to finalize the exits by adding a ref to
    # guid of the other area
    #exits = [ p for p in props if p[1].get('group', None) == 'door' ]
    #for gid, prop in exits:
    #    x, y, l = toWorld(data, data.getTileLocation(gid)[0])
    #    area.exits[prop['guid']] = ((x, y, l), None)

    return area

