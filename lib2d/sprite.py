"""
sprite-like classes for transition from pygame
supports animation, flipping, is pickleable, etc
includes pymunk integration
new python language features used
"""

import pymunk



class Sprite(object):
    """simple base class for visible game objects
    pygame.sprite.Sprite(*groups): return Sprite

    The base class for visible game objects. Derived classes will want to 
    override the Sprite.update() and assign a Sprite.image and 
    Sprite.rect attributes.  The initializer can accept any number of 
    Group instances to be added to.

    When subclassing the Sprite, be sure to call the base initializer before
    adding the Sprite to Groups.
    """

    def __init__(self, *groups):
        self.__g = {}                       # The groups the sprite is in
        if groups: self.add(groups)

    def add(self, *groups):
        """
        add the sprite to groups
        Sprite.add(*groups): return None

        Any number of Group instances can be passed as arguments. The 
        Sprite will be added to the Groups it is not already a member of.
        """
        has = self.__g.__contains__
        for group in groups:
            if hasattr(group, '_spritegroup'):
                if not has(group):
                    group.add_internal(self)
                    self.add_internal(group)
            else: self.add(*group)

    def remove(self, *groups):
        """
        remove the sprite from groups
        Sprite.remove(*groups): return None

        Any number of Group instances can be passed as arguments. The Sprite
        will be removed from the Groups it is currently a member of.
        """
        has = self.__g.__contains__
        for group in groups:
            if hasattr(group, '_spritegroup'):
                if has(group):
                    group.remove_internal(self)
                    self.remove_internal(group)
            else: self.remove(*group)

    def add_internal(self, group):
        self.__g[group] = 0

    def remove_internal(self, group):
        del self.__g[group]

    def update(self, *args):
        """
        method to control sprite behavior
        Sprite.update(*args):

        The default implementation of this method does nothing; it's just a
        convenient "hook" that you can override. This method is called by
        Group.update() with whatever arguments you give it.

        There is no need to use this method if not using the convenience 
        method by the same name in the Group class.
        """
        pass

    def kill(self):
        """
        remove the Sprite from all Groups
        Sprite.kill(): return None

        The Sprite is removed from all the Groups that contain it. This won't
        change anything about the state of the Sprite. It is possible to
        continue to use the Sprite after this method has been called, including
        adding it to Groups.
        """
        for c in self.__g.keys():
            c.remove_internal(self)
        self.__g.clear()

    def groups(self):
        """list of Groups that contain this Sprite
        Sprite.groups(): return group_list

        Return a list of all the Groups that contain this Sprite.
        """
        return self.__g.keys()

    def alive(self):
        """does the sprite belong to any groups
        Sprite.alive(): return bool

        Returns True when the Sprite belongs to one or more Groups.
        """
        return (len(self.__g) != 0)

    def __repr__(self):
        return "<{} sprite(in {} groups)>".format(
            self.__class__.__name__, len(self.__g)
        )


class AbstractGroup(object):
    """
    A base for containers for sprites. It does everything needed to behave as a
    normal group. You can easily inherit a new group class from this, or the
    other groups below, if you want to add more features.

    Any AbstractGroup-derived sprite groups act like sequences, and support
    iteration, len, and so on.
    """

    # dummy val to identify sprite groups, and avoid infinite recursion.
    _spritegroup = True

    def __init__(self):
        self.spritedict = {}
        self.lostsprites = []

    def sprites(self):
        """sprites()
           get a list of sprites in the group

           Returns an object that can be looped over with a 'for' loop.
           (For now it is always a list, but newer version of Python
           could return different iterators.) You can also iterate directly
           over the sprite group."""
        return list(self.spritedict.keys())

    def add_internal(self, sprite):
        self.spritedict[sprite] = 0

    def remove_internal(self, sprite):
        r = self.spritedict[sprite]
        if r is not 0:
            self.lostsprites.append(r)
        del(self.spritedict[sprite])

    def has_internal(self, sprite):
        return sprite in self.spritedict

    def copy(self):
        """copy()
           copy a group with all the same sprites

           Returns a copy of the group that is the same class
           type, and has the same sprites in it."""
        return self.__class__(self.sprites())

    def __iter__(self):
        return iter(self.sprites())

    def __contains__(self, sprite):
        return self.has(sprite)

    def add(self, *sprites):
        """add(sprite, list, or group, ...)
           add sprite to group

           Add a sprite or sequence of sprites to a group."""
        for sprite in sprites:
            # It's possible that some sprite is also an iterator.
            # If this is the case, we should add the sprite itself,
            # and not the objects it iterates over.
            if isinstance(sprite, Sprite):
                if not self.has_internal(sprite):
                    self.add_internal(sprite)
                    sprite.add_internal(self)
            else:
                try:
                    # See if sprite is an iterator, like a list or sprite
                    # group.
                    for spr in sprite:
                        self.add(spr)
                except (TypeError, AttributeError):
                    # Not iterable, this is probably a sprite that happens
                    # to not subclass Sprite. Alternately, it could be an
                    # old-style sprite group.
                    if hasattr(sprite, '_spritegroup'):
                        for spr in sprite.sprites():
                            if not self.has_internal(spr):
                                self.add_internal(spr)
                                spr.add_internal(self)
                    elif not self.has_internal(sprite):
                        self.add_internal(sprite)
                        sprite.add_internal(self)

    def remove(self, *sprites):
        """remove(sprite, list, or group, ...)
           remove sprite from group

           Remove a sprite or sequence of sprites from a group."""
        # This function behaves essentially the same as Group.add.
        # Check for Spritehood, check for iterability, check for
        # old-style sprite group, and fall back to assuming
        # spritehood.
        for sprite in sprites:
            if isinstance(sprite, Sprite):
                if self.has_internal(sprite):
                    self.remove_internal(sprite)
                    sprite.remove_internal(self)
            else:
                try:
                    for spr in sprite: self.remove(spr)
                except (TypeError, AttributeError):
                    if hasattr(sprite, '_spritegroup'):
                        for spr in sprite.sprites():
                            if self.has_internal(spr):
                                self.remove_internal(spr)
                                spr.remove_internal(self)
                    elif self.has_internal(sprite):
                        self.remove_internal(sprite)
                        sprite.remove_internal(self)

    def has(self, *sprites):
        """has(sprite or group, ...)
           ask if group has a sprite or sprites

           Returns true if the given sprite or sprites are
           contained in the group. You can also use 'sprite in group'
           or 'subgroup in group'."""
        # Again, this follows the basic pattern of Group.add and
        # Group.remove.
        for sprite in sprites:
            if isinstance(sprite, Sprite):
                return self.has_internal(sprite)

            try:
                for spr in sprite:
                    if not self.has(spr):
                        return False
                return True
            except (TypeError, AttributeError):
                if hasattr(sprite, '_spritegroup'):
                    for spr in sprite.sprites():
                        if not self.has_internal(spr):
                            return False
                    return True
                else:
                    return self.has_internal(sprite)

    def update(self, *args):
        """update(*args)
           call update for all member sprites

           calls the update method for all sprites in the group.
           Passes all arguments on to the Sprite update function."""
        for s in self.sprites(): s.update(*args)

    def draw(self, surface):
        """draw(surface)
           draw all sprites onto the surface

           Draws all the sprites onto the given surface."""
        sprites = self.sprites()
        surface_blit = surface.blit
        for spr in sprites:
            self.spritedict[spr] = surface_blit(spr.image, spr.rect)
        self.lostsprites = []

    def clear(self, surface, bgd):
        """clear(surface, bgd)
           erase the previous position of all sprites

           Clears the area of all drawn sprites. the bgd
           argument should be Surface which is the same
           dimensions as the surface. The bgd can also be
           a function which gets called with the passed
           surface and the area to be cleared."""
        try:
            bgd.__call__
        except AttributeError:
            pass
        else:
            for r in self.lostsprites:
                bgd(surface, r)
            for r in self.spritedict.values():
                if r is not 0: bgd(surface, r)
            return
        surface_blit = surface.blit
        for r in self.lostsprites:
            surface_blit(bgd, r, r)
        for r in self.spritedict.values():
            if r is not 0: surface_blit(bgd, r, r)

    def empty(self):
        """empty()
           remove all sprites

           Removes all the sprites from the group."""
        for s in self.sprites():
            self.remove_internal(s)
            s.remove_internal(self)

    def __nonzero__(self):
        return (len(self.sprites()) != 0)

    def __len__(self):
        """len(group)
           number of sprites in group

           Returns the number of sprites contained in the group."""
        return len(self.sprites())

    def __repr__(self):
        return "<%s(%d sprites)>" % (self.__class__.__name__, len(self))


class RenderGroup(AbstractGroup):
    """
    This group is capable of rendering sprites to a surface.

    This group can be conceptualized as a "camera".
    """
    
    def __init__(self, *sprites):
        AbstractGroup.__init__(self)
        self.add(*sprites)

    def draw(self, surface):
        
