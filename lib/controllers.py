"""
commands for the main character
"""

from actions import *
from lib2d import context
from lib2d.buttons import *
from lib2d.fsm import *



# =============================================================================
# context transition pickers

class transition(object):
    def __call__(self, *arg, **kwarg):
        return self.pick(*arg, **kwarg)

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def pick(self, parent, entity):
        pass


class dieT(transition):
    def pick(self, parent, entity):
        return deadState()


class fallingT(transition):
    def pick(self, parent, entity):
        return FallAction()


class checkFallingT(transition):
    def pick(self, parent, entity):
        body = entity.body
        if abs(entity.grounding['impulse'].y) / body.mass == 0:
            return FallAction()
        else:
            return None


class idleT(transition):
    def pick(self, parent, entity):
        body = entity.body
        if body.velocity.y > 0:
            parent.append(IdleAction())
            return FallAction()

        return IdleAction()


class unbrakeT(transition):
    def pick(self, parent, entity):
        return UnbrakeAction()


class brakeT(transition):
    def pick(self, parent, entity):
        body = entity.body
        friction = body.velocity.x * body.mass * entity.parent.gravity[1]
        if abs(body.velocity.x) >= entity.max_speed*20:
            return BrakeAction()
        else:
            return None


class moveT(transition):
    def pick(self, parent, entity):
        return MoveAction()


class crouchT(transition):
    def pick(self, parent, entity):
        body = entity.body
        if abs(body.velocity.x) > 1.2:
            return RollAction()
        else:
            return CrouchAction()


class uncrouchT(transition):
    def pick(self, parent, entity):
        return UncrouchAction()


class upT(transition):
    def pick(self, parent, entity):
        return JumpAction()

class fallRecoverT(transition):
    def pick(self, parent, entity):
        body = entity.body
        if abs(body.velocity.x) >= SPRINT_SPEED:
            return RollAction()
        else:
            return fallRecoverState()

class jumpT(transition):
    def pick(self, parent, entity):
        return JumpAction()

class wallJumpT(transition):
    def pick(self, parent, entity):
        return wallJumpState()

class airmoveT(transition):
    def pick(self, parent, entity):
        return AirMoveAction()

class checkWallGrabT(transition):
    def pick(self, parent, entity):
        return wallGrabState()

die = dieT()
idle = idleT()
brake = brakeT()
unbrake = unbrakeT()
move = moveT()
crouch = crouchT()
uncrouch = uncrouchT()
up = upT()
fallRecover = fallRecoverT()
jump = jumpT()
checkFalling = checkFallingT()
walljump = wallJumpT()
airmove = airmoveT()
checkWallGrab = checkWallGrabT()
fall = fallingT()


# =============================================================================
# transition formulas

# context will be automatically canceled when the button is released
def toggle(source, trigger, ctx, picker):
    return (source, trigger, BUTTONDOWN), ctx, picker, (source, trigger, BUTTONUP)

# new_ctx will be run whenever old_ctx finishes
def endState(ctx, picker):
    return (ctx, STATE_VIRTUAL, STATE_FINISHED), None, picker

# new_context will be run when transitioning from ctx0 to ctx1
def inject(ctx0, ctx1, picker):
    return (ctx0, STATE_VIRTUAL, STATE_FINISHED), ctx1, picker

# new_ctx will be run when there is a collision during old_ctx
# this formula is not completely supported yet
def collision(ctx, picker):
    return (ctx, STATE_VIRTUAL, COLLISION), ctx, picker

#
# =============================================================================

class HeroController(InputFSM):

    def program(self, source):

        # walking
        self.at(*toggle(source, P1_LEFT, IdleAction, move))
        self.at(*toggle(source, P1_RIGHT, IdleAction, move))

        # brake animation after a sprint
        self.at(*inject(MoveAction, IdleAction, brake))

        # allow walking to cancel from walking or braking
        self.at(*toggle(source, P1_LEFT, MoveAction, move),flags=BREAK)
        self.at(*toggle(source, P1_RIGHT, MoveAction, move),flags=BREAK)
        self.at(*toggle(source, P1_LEFT, UnbrakeAction, move),flags=QUEUED)
        self.at(*toggle(source, P1_RIGHT, UnbrakeAction, move),flags=QUEUED)
        self.at(*toggle(source, P1_LEFT, BrakeAction, move),flags=QUEUED)
        self.at(*toggle(source, P1_RIGHT, BrakeAction, move),flags=QUEUED)

        # allow uncrouch animation to be canceled (skipped)
        self.at(*toggle(source, P1_LEFT, UncrouchAction, move))
        self.at(*toggle(source, P1_RIGHT, UncrouchAction, move))

        # play unbrake animation after the brake animation
        self.at(*endState(BrakeAction, unbrake))


        # moving in the air
        self.at(*toggle(source, P1_LEFT, JumpAction, airmove))
        self.at(*toggle(source, P1_RIGHT, JumpAction, airmove))
        self.at(*toggle(source, P1_LEFT, FallAction, airmove))
        self.at(*toggle(source, P1_RIGHT, FallAction, airmove))

        # allow air animation to cancel on left or right
        self.at(*toggle(source, P1_LEFT, AirMoveAction, airmove), flags=BREAK)
        self.at(*toggle(source, P1_RIGHT, AirMoveAction, airmove), flags=BREAK)

        # if colliding during airmove, then check if player can grab wall
        #self.at(*collision(AirMoveAction, checkWallGrab), flags=BREAK)

        # wall jumping
        #self.at((source, P1_ACTION2, BUTTONDOWN), wallGrabState, walljump, flags=BREAK)


        # crouch
        self.at(*toggle(source, P1_DOWN, IdleAction, crouch))

        # roll
        self.at((source, P1_DOWN, BUTTONDOWN), MoveAction, crouch)

        # allow crouching to cancel into crouching
        #self.at(*toggle(source, P1_DOWN, CrouchAction, crouch), flags=BREAK)
        #self.at(*toggle(source, P1_DOWN, UncrouchAction, crouch), flags=BREAK)

        # play uncrouch animation after crouching
        self.at(*endState(CrouchAction, uncrouch))

        # roll recovers after big jumps
        #self.at((source, P1_DOWN, BUTTONDOWN), fallRecoverState, crouch)
        #self.at((source, P1_DOWN, BUTTONDOWN), RollAction, crouch)

        # play uncrouch animation after a roll
        self.at(*endState(RollAction, uncrouch))


        # jumping
        self.at((source, P1_ACTION2, BUTTONDOWN), IdleAction, jump)
        self.at((source, P1_ACTION2, BUTTONDOWN), MoveAction, jump)

        # double jump
        #self.at((source, P1_ACTION2, BUTTONDOWN), JumpAction, jump, flags=BREAK)
        #self.at((source, P1_ACTION2, BUTTONDOWN), FallAction, jump, flags=BREAK)

        # falling after a jump
        #self.at(*endState(JumpAction, fall))


    def primestack(self):
        self.append(IdleAction())


    def reset(self):
        for ctx in reversed(self._stack):
            self.remove(ctx)

        self.time = 0
        self.holds = {}
        self.move_history = []
        self.last_context = None
        self.primestack()
