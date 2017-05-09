from time import time
import math

from actor import Actor
import mmath as mm


class PhysicsActor(Actor):
    def __init__( self, name_s:str, initPos_t:tuple=(0.0, 0.0, 0.0) ):
        super().__init__( name_s, None, initPos_t, False )

        self.__lastUpdateTime_f = time()
        self.__lastApplyedPos_t = self.getPosXYZ()

        self.__standingOnGroud_b = False

        self.__jumpGravity_f = 0.0
        self.__gravity_f = 5.0

        self.__xInput_f = 0.0
        self.__zInput_f = 0.0

        self.__xMomentum_f = 0.0
        self.__zMomentum_f = 0.0

        self.__movedABit_b = False

    def applyPhysics(self, freeze_b:bool) -> None:
        timeDelta_f = self.__precalculateConditions()
        if freeze_b:
            return

        self.__horizontalMove(timeDelta_f)

        if self.__jumpGravity_f > 0.0:
            gravity_f = timeDelta_f * self.__jumpGravity_f
            self.setPosY( self.getPosY() + gravity_f )

        gravity_f = timeDelta_f*self.__gravity_f
        if gravity_f < -0.5:
            gravity_f = -0.5
        self.setPosY( self.getPosY() + gravity_f )

        self.__movedABit_b = False
        self.__lastApplyedPos_t = self.getPosXYZ()

    def giveHorizontalMomentum(self, x:float, z:float):
        self.__xInput_f = x
        self.__zInput_f = z

        if x or z:
            self.__movedABit_b = True
        else:
            self.__movedABit_b = False

    def __horizontalMove(self, timeDelta_f:float):

        self.setPosX( self.getPosX() + self.__xInput_f*timeDelta_f*8 )
        self.setPosZ( self.getPosZ() + self.__zInput_f*timeDelta_f*8 )



    def __precalculateConditions(self) -> float:
        thisTime_f = time()
        timeDelta_f = thisTime_f - self.__lastUpdateTime_f
        self.__lastUpdateTime_f = thisTime_f

        if self.getPosY() > self.__lastApplyedPos_t[1]:  # Stand on the groud
            self.__standingOnGroud_b = True
        else:
            self.__standingOnGroud_b = False

        if self.__lastApplyedPos_t[1] > self.getPosY():  # Head reached ceiling.
            self.__jumpGravity_f = 5.0

        if self.__standingOnGroud_b:
            self.__gravity_f = -1.0
            self.__jumpGravity_f = 0.0
        else:
            self.__gravity_f += timeDelta_f * -20.0
            if self.__gravity_f < -100.0:
                self.__gravity_f = -100.0

        return timeDelta_f

    def startJumping(self) -> None:
        if self.__standingOnGroud_b:
            self.__lastApplyedPos_t = self.getPosXYZ()
            self.__standingOnGroud_b = False
            self.__jumpGravity_f = 8.0
