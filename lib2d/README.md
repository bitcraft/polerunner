Lib2d
=====

Lib2d is a game engine that I have been developing to create PyWeek games.


What it does
------------

    State (context) management
    Animated Sprites with multiple animations and automatic flipping
    Integrated Tiled Map (TMX) support
    Fast, efficient tilemap rendering with parallax support
    Basic GUI features
    Integrated Chipmunk dynamics (pymunk)
    Advanced AI (pygoap)
    Integrated animation and input handling (fsa.py)
    Simplified save game support
    Dialogs, menus and other simple GUI elements
    Uses pygame for the input, rendering, sound and music playback.
    Lib2d is effiecent: generator expressions and iterators are used in excess


Concept
-------

    Lib2d breaks game design and development into 3 parts:
    * Level Maps built in Tiled
    * Game entities defined in buildworld.py
    * Game entities programmed using Lib2d objects

    Because of the close integration with Tiled, Lib2d must be used it it.


Tiled Integration
-----------------

    Lib2d uses PyTMX to load TMX level files.  Lib2d requires the designer to
    follow a few rules when creating maps.  These specially formatted maps
    can be loaded and run directly from Lib2d.


Game Entities
-------------

    Lib2d game entites (players, npcs, collectable objects, etc) all have a
    unique number assinged to them called the GUID.  This number can be
    directly assigned to an object or can be automatically assigned by the
    game.


Lib2d Objects
-------------

    Lib2d objects are created and stored in an object hierarchy that can be
    safely written to disk and restored later.  This unifies game creation and
    save game functionality.  In fact, buildworld.py is simply a script to
    create a blank 'save game'.


Game Structure Overview
-----------------------

    Map is designed in Tiled with special layer (controlset.tsx)
    Game objects are created in world.py and assigned GUID control numbers
    The 'world' data structure is pickleable and becomes the save game
    When engine is started, the world data structure can be used to play


Control
-------

    Lib2d wraps all pygame events for player input so they can be remapped.
    It also make keyboard and joystick controls interchangeable at runtime.
    Using fsa.py, instead of coding the behavour of the controls, you can
    use a finite state machine to define how the character changes states.

    Traditional pygame/sdl event handling can occur alongside Lib2d's system.

    Lib2d GUI elements are able to interact with the mouse


Tilemap
-------

    The tilemap uses a special surface that gets updated in the background
    (or by another thread).  It performs very well when scrolling.  Large TMX
    maps can be used since only the visible portions of the map are rendered.


Physics
-------

    The library uses pymunk and cannot work without it.  The obvious benefits
    are a fast physics system (not more colliding rects!) and it has good
    integration with the TMX loader.

    You can define your walls in tiles, and they will get loaded into the
    Chipmunk engine automatically.


GUI
---

    The element class includes allows the programmer to define how screen space
    is divided up.  Objects inheriting from it can be resized and moved without
    much effort.

    Elements are mouse-aware and can be interacted with the mouse.


Development
-----------

- all classes need to be scanned for unpickleable values
- physics in area.py need to have a save and load state
- sound model needs to be re-imagined
- level warps need to be fixed
- the concurrency model (context.py) should be pervasive
- fsa.py should have nicer programming syntax
