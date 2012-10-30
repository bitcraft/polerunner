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
from lib2d import res, draw, context

import pygame, os



class TextDialog(context.Context):
    """
    State that takes focus and waits for player to press a key
    after displaying some some text.
    """

    # works well for the defualt font and size 
    wrap_width = 44 
 
    wait_sound = res.loadSound("select0.wav")
    wait_sound.set_volume(0.40)

    borderImage = Image("lpc-border0.png", colorkey=True)


    def activate(self):
        self.background = (109, 109, 109)
        self.border = draw.GraphicBox(self.borderImage)
        self.redraw = True
        self.activated = True


    # just write the text and wait for a keypress
    def prompt(self, text, title=None):
        self.text = text
        self.title = title


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
            self.done()


class ChoiceDialog(context.Context):
    #wrap_width = 58 # font 12
    
    text_size = 14
    wrap_width = 46 
 
    background = (128, 128, 128)

    wait_sound = res.loadSound("select0.wav")
    wait_sound.set_volume(0.20)

    def __init__(self, text, choices, title=None):
        context.Context.__init__(self)
        self.text = text
        self.state = 0
        self.counter = 0
        self.title = title
        self.choices = choices

    # when given focus for first time
    def activate(self):
        xsize = 300
        ysize = 70
        bkg = Surface((xsize, ysize))
        bkg.lock()
        bkg.fill((128,128,128))
        for i in range(1, 4):
            draw.rect(bkg,(i*32,i*32,i*32),(4-i,4-i,xsize+(i-4)*2,ysize+(i-4)*2),3)

        corner = (64,64,64)
        bkg.set_at((0,0), corner)
        bkg.set_at((xsize,0), corner)
        bkg.set_at((xsize,ysize), corner)
        bkg.set_at((0,ysize), corner)

        bkg.unlock()

        bkg.set_alpha(64)

        self.bkg = bkg

        if self.title != None:
            banner = OutlineTextBanner(self.title, (200,200,200), 20)
            self.title_image = banner.render()
            self.title_image.set_alpha(96)

        self.arrow = res.loadImage("wait_arrow.png", colorkey=1)

    # when focus is given again
    def reactivate(self):
        pass

    # when losing focus
    def deactivate(self):
        pass

    def draw(self, surface):
        # fade in the dialog box background
        if self.state == 0:
            surface.blit(self.bkg, (10,160))
            self.counter += 1
            if self.counter == 6:
                self.bkg.set_alpha(0)
                self.bkg = self.bkg.convert()
            elif self.counter == 7:
                surface.fill((128,128,128), (14, 146, self.bkg.get_size()))
                self.counter = 0
                self.state = 1
                self.bkg = None

        # fade in the title, if any
        elif self.state == 1:
            if self.title != None:
                surface.blit(self.title_image, (15,150))
                self.counter += 1
                if self.counter == 3:
                    self.state = 2
                    self.counter = 0
                    self.title_image = None
            else:
                self.state = 2

        # quickly write the text
        elif self.state == 2:
            x = 20

            if self.title != None:
                y = 168
            else:
                y = 167

            for line in wrap(self.text, self.wrap_width):
                banner = TextBanner(line, size=self.text_size)
                surface.blit(banner.render(self.background), (x,y))
                y += banner.font.size(line)[1]

            self.menu = cMenu(Rect((25,210),(280, 30)),
                5, 5, 'horizontal', 10,
                [('Yes', self.yes),
                ('No', self.no)],
                font="fonts/dpcomic.ttf", font_size=16)

            self.menu.ready()
            self.wait_sound.stop()
            self.wait_sound.play()
            self.state = 3

        elif self.state == 3:
            self.menu.draw(surface)

    def handle_event(self, event):
        if self.state > 2:
            self.menu.handle_event(event)

    def choice0(self): pass
    def choice1(self): pass
    def choice2(self): pass
    def choice3(self): pass

    def yes(self): sd.done()
    def no(self): sd.done()
