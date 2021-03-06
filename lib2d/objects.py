import res, context
import pygame, types, os

unsupported = [pygame.Surface, types.MethodType]


def loadObject(name):
    """
    read this node from disk
    """

    import cPickle as pickle

    with open(name + "-data.save") as fh:
        node = pickle.load(fh)

    return node


class GameObject(object):
    """
    Essentially, game objects are part of a simple tree data structure.
    The top node will not have the parent set.

    Implements:
        - context protocol
        - iterator protocol
    """
    acceptableChildren = None

    def __init__(self, children=[], parent=None, guid=None):
        # hack
        if self.acceptableChildren == None:
            self.acceptableChildren = (GameObject,)

        self.guid = guid
        self.parent = None
        self._children = []
        self._loaded = False

        if parent is not None:
            self.parent = parent

        if not isinstance(children, (list, tuple)):
            children = [children]

        [ self.add(child) for child in children ]

        # cache
        self._avatar = None

    def __repr__(self):
        return "<{}: \"{}\">".format(self.__class__.__name__, id(self))

    def __contains__(self, child):
        return child in self._children

    def __iter__(self):
        return iter(self._children)

    def __enter__(self):
        self.enter()

    def __exit__(self):
        self.exit()

    def enter(self):
        """
        Called after focus is given to the context
        This may be called several times over the lifetime of the context
        """
        pass

    def exit(self):
        """
        Called after focus is lost
        This may be called several times over the lifetime of the context
        """
        pass

    def of_class(self, klass):
        """
        Return iterator object of all children that are subclass of <class>
        """
        for i in self:
            if isinstance(i, klass):
                yield i

    @property
    def avatar(self):
        """
        Convenience function that returns the avatar of this node
        """
        if self._avatar is None:
            import avatar
            for child in self._children:
                if isinstance(child, avatar.Avatar):
                    self._avatar = child
                    return child
            else:
                self._avatar = False
                return None
        else:
            return self._avatar

    @property
    def sounds(self):
        """
        Convenience function that returns the sounds of this node
        """
        import sound
        return self.of_class(sound.Sound)

    def returnNew(self):
        """
        override this if the constructor requires any special arguments
        """

        try:
            return self.__class__()
        except TypeError:
            msg = "Class {} is not cabable of being copied."
            raise TypeError, msg.format(self.__class__)

    def copy(self):
        new = self.returnNew()

        new.__dict__.update(self.__dict__)
        new._parent = None
        new._children = []
        new._childrenGUID = []
        new.guid = None

        for child in self._children:
            new.add(child.copy())

        return new 

    def loadAll(self):
        """
        Load this object and the all children of it.
        """
        self.__load__()

    def __load__(self):
        """
        Do not override this.  Use load instead.
        """
        print "__LOAD__", self
        [ child.__load__() for child in self._children ]
        self.load()
        [ child.post_load() for child in self._children ]

    def load(self):
        """
        If any data needs to be read from disk, do it here.

        This hook will be called *after* all the children have been loaded.

        NOTE: The parent only loads after all of the children have loaded, so
              if this object requires any data in the parent that needs to be
              loaded too, then you will have to use the post_load hook.
        """
        pass

    def post_load(self):
        """
        If this object needs any data from the parent that may not be ready
        during load, then use this hook.  This will be called after the parent
        has loaded completely.
        """
        pass

    def unload(self):
        """
        Anything that could be removed from memory should be removed here
        """
        pass

    @property
    def parent(self):
        """
        Return the parent of this node
        """
        return self._parent

    @parent.setter
    def parent(self, node):
        self._parent = node

    @property
    def guid(self):
        return self._guid

    @guid.setter
    def guid(self, guid):
        if guid is None:
            self._guid = None
            return

        try:
            self._guid = int(guid)
        except:
            raise ValueError, "GUID's must be an integer"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def remove(self, child):
        """
        Remove a child node
        """
        try:
            self._children.remove(child)
            child._parent = None
        except ValueError:
            msg = "Attempting to remove child ({}), but not in parent ({})"
            raise ValueError, msg.format(child, self)

    def add(self, child):
        """
        Add a child node
        """
        ok=False
        for klass in self.acceptableChildren:
            if isinstance(child, klass):
                ok=True
                break
        else:
            print self, child.__class__, self.acceptableChildren
            raise valueError

        self._children.append(child)
        try:
            if child._parent:
                child._parent.remove(child)
        except:
            print 'Error taking {} from parent.  Ignored'.format(child)
            pass

        child.parent = self

    def hasChild(self, child):
        for c in self.getChildren():
            if c == child: return True
        return False

    def getChildren(self):
        # should be a breadth-first search
        children = []
        openList = [self]
        while openList:
            parent = openList.pop()
            children = parent._children[:]
            while children:
                child = children.pop()
                openList.append(child)
                yield child

    @property
    def root(self):
        node = self
        while node._parent is not None:
            node = node._parent
        return node

    def getChildByGUID(self, guid):
        """
        search the children of this object for an object
        with the matching guid
        """
      
        guid = int(guid) 
        if self.guid == guid: return self 
        for child in self.getChildren():
            if child.guid == guid: return child

        msg = "GUID ({}) not found."
        raise Exception, msg.format(guid)

    def getChildByName(self, name):
        for child in self.getChildren():
            if child.name == name: return child

        msg = "Object by name ({}) not found."
        raise Exception, msg.format(name)

    def serialize(self, pickler, callback=None):
        """
        pickle this object, and continue with the children
        """

        pickler.dump(self)

        if callback:
            callback(self, pickler)

        for child in self._children:
            child.serialize(pickler, callback)

    def destroy(self, parent=None):
        """
        destroy the object and children.  the object will be removed from the
        game and references cleared.
        """

        name = "DEAD-{}".format(self.name)
        if self._parent:
            self._parent.remove(self)
        for child in self._children:
            child.destroy()
        self._children = []
        self.unload()
        self.name = name

    def save(self, name):
        """
        write the state of this object and all of its children to disk.
        it will be a pair of files.
        """

        import cPickle as pickle
        import StringIO

        def testRun():
            for child in self.getChildren():
                for k, v in child.__dict__.items():
                    if type(v) in unsupported:
                        print "Object {} contains unpickleable attribute \"{}\" {} ({})".format(child, k, type(v), v)
                        raise ValueError

        # generate unique ID's for all the objects (if not already assigned)
        # saving is only ever done for the top level node
        # if saving children of it, then guid may not be unique

        i = 0
        used = set([ child.guid for child in self.getChildren() ])
        used.add(self.guid)
        for child in self.getChildren():
            if child.guid: continue
            while i in used:
                i += 1
            child.setGUID(i)
            used.add(i)

        testRun()

        toc = {}
        def handleWrite(obj, pickler):
            toc[obj.guid] = fh.tell()

        with open(name + "-data.temp", "w") as fh:
            pickler = pickle.Pickler(fh, -1)
            self.serialize(pickler, handleWrite)

        os.rename(name + "-data.temp", name + "-data.save")

        #with open(name + "-index.txt", "w") as fh:
        #    pickler = pickle.Pickler(fh, -1)
        #    pickler.dump(toc)


class InteractiveObject(GameObject):
    """
    object that exists in the game world
    excludes things like animations and ui elements which are saved, but
    don't require things like physics simulation
    """

    def use(self, user=None):
        pass
