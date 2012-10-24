from entity import Entity

import random



class HoverBot(Entity):
    sounds = ["hover0.wav", "whiz0.wav", "startupfail1.wav"]

    time_update = True
    time = 0
    last_hover = 0


    def hover(self, multiplier):
        body = self.parent.getBody(self)

        if multiplier >= 80:
            self.parent.emitSound("startupfail1.wav", ttl=1000, thing=self)
        elif body.vel.z > .2:
            self.parent.emitSound("whiz0.wav", ttl=400, thing=self)
        else:
            self.parent.emitSound("hover0.wav", ttl=100, thing=self)


        self.avatar.play("hover")
        self.last_hover = self.time
        body.acc.z -= self.parent.physicsgroup.gravity_delta.z * multiplier


    def update(self, time):
        """
        do some cool hackery here
        
        we assume the lbrary is updating the physics 5x to one draw and the
        fps is locked at 40, so we can easily simulate thrusters levitating
        the robot.
        """

        body = self.parent.getBody(self)

        self.time += time
        if self.time >= self.last_hover + 300:
            self.avatar.play("fall")

        # if true we are falling
        if body.vel.z > .05:

            # test if robot is hovering over the ground
            # find how far away the ground is (not a great way to do this)
            distance = 16
            bbox = body.bbox.copy()
            bbox.move(0,0,distance)

            while self.parent.physicsgroup.testCollision(bbox):
                distance -= 1
                bbox = body.bbox.copy()
                bbox.move(0,0,distance)


            freq = round(distance/16.0 * 3)

            # make the robot a bit wonky
            if random.randint(0,freq) == 0:

                if distance == 16:
                    self.hover(2)
                else:
                    body.vel.z = body.vel.z / 2.0
                    body.acc.z = 0
                    self.hover(40)

        elif body.vel.z == 0:
            bbox = body.bbox.copy()
            bbox.move(0,0,1)

            if self.parent.physicsgroup.testCollision(bbox):
                self.hover(80)

        if body.vel.z < -.1:
            body.vel.z = -.1
