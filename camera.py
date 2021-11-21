from typing import Tuple

import numpy as np

from actor import Actor
import mmath


class Camera(Actor):
    def __init__( self, name_s:str, parent:Actor=None, initPos:Tuple[float, float, float]=(0, 0, 0) ):
        super().__init__( name_s, parent, initPos )

    def getViewMatrix(self) -> np.ndarray:
        ver, hor, _ = self.getWorldDegreeXYZ()

        return mmath.getTranslateMat4(*self.getWorldXYZ(), -1).dot(
            mmath.getRotateXYZMat4(hor, 0, 1, 0)
        ).dot(mmath.getRotateXYZMat4(ver, 1, 0, 0))

    def getLookingVec(self) -> mmath.Vec4:
        ver, hor, _ = self.getWorldDegreeXYZ()
        vec = mmath.Vec4(0, 0, -1)
        vec = vec.transform(mmath.getRotateXYZMat4(-ver, 1, 0, 0), mmath.getRotateXYZMat4(-hor, 0, 1, 0)).normalize()
        return vec
