"""
Copyright 2010, 2011  Leif Theden


This file is part of lib2d.

lib2d is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

lib2d is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with lib2d.  If not, see <http://www.gnu.org/licenses/>.
"""

from lib2d.buttons import *
from lib2d.ui import Menu
from lib2d.image import Image
from lib2d.objects import loadObject
from lib2d import res, draw, game

import pygame, os



class TextDialog(game.GameContext):
    """
    State that takes focus and waits for player to press a key after displaying
    some some text.
    """

    wait_sound = res.loadSound("select0.wav")
    wait_sound.set_volume(0.40)

    borderImage = Image("lpc-border0.png", colorkey=True)


    def __init__(self, text, title=None):
        self.text = text
        self.title = title


    def enter(self):
        self.background = (109, 109, 109)
        self.border = draw.GraphicBox(self.borderImage)
        self.activated = True
        self.redraw = True


    def draw(self, surface):
        if self.redraw:
            self.redraw = False

            sw, sh = surface.get_size()

            # draw the border
            x, y = 0.0313 * sw, 0.6667 * sh
            w, h = 0.9375 * sw, 0.2917 * sh
            self.border.draw(surface, (x, y, w, h), fill=True)
           
            fullpath = res.fontPath("dpcomic.ttf")
            fontSize = int(0.0667 * sh)
            font = pygame.font.Font(fullpath, fontSize)

            # adjust the margins of text if there is a title
            if self.title:
                x = 0.0625 * sw
                y = 0.7 * sh

            draw.drawText(surface, self.text, (0,0,0), (x+10,y+8,w-18,h-12),
                         font, aa=1, bkg=self.background)
            
            # print the title
            if self.title != None:
                banner = OutlineTextBanner(self.title, (200,200,200),
                                           int(fontSize*1.25), font=self.font)
                title_image = banner.render()
                x, y = 0.4688 * sw, 0.625 * sh
                surface.blit(title_image, (x, y))

            # show arrow
            #x, y = 0.0625 * sw, 0.9167 * sh
            #arrow = res.loadImage("wait_arrow.png", colorkey=1)
            #surface.blit(arrow, (x, y))

            # play a nice sound 
            self.wait_sound.stop()
            self.wait_sound.play()


    def handle_command(self, cmd):
        if cmd[1] == P1_ACTION1 and cmd[2] == BUTTONDOWN:
            self.parent.remove(self)

