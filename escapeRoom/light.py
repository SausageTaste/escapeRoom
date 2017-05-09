from math import cos

import numpy as np
import OpenGL.GL as gl

from actor import ActorGeneral
import mmath


class PointLight(ActorGeneral):
    def __init__(self, name_s, static_b, initPos_t, color_t, maxDistance_f:float):
        super().__init__(name_s, static_b, initPos_t)

        self.color_t = color_t
        self.maxDistance_f = maxDistance_f

    def __repr__(self) -> str:
        return "< {}.PointLight object at 0x{:0>16X}, name: {}, pos: {}, color: {}, maxDist: {} >".format(
            __name__, id(self), self.getName(), self.getPosXYZ(), self.color_t, self.maxDistance_f
        )


class SpotLight(ActorGeneral):
    def __init__(self, name_s, static_b, initPos_t, color_t, maxDistance_f:float, cutoffDegree_f:float):
        super().__init__(name_s, static_b, initPos_t)

        self.color_t = color_t
        self.maxDistance_f = float(maxDistance_f)

        self.cutoffDegree_f = float(cutoffDegree_f)
        self.cutoff_f = cos(mmath.Angle(cutoffDegree_f).getRadian())

        self.__depthMapFbo = None
        self.depthMapTex = None

        self.__shadowW_i = 256
        self.__shadowH_i = 256

    def getLookingVec(self, parent) -> mmath.Vec4:
        ver, hor, _ = self.getWorldDegreeXYZ(parent)
        vec = mmath.Vec4(0, 0, -1)
        vec = vec.transform(mmath.getRotateXYZMat4(-ver, 1, 0, 0), mmath.getRotateXYZMat4(-hor, 0, 1, 0)).normalize()
        return vec

    def getPerspectiveMatrix(self) -> np.ndarray:
        return mmath.getPerspectiveMat4(self.cutoffDegree_f * 2.0, 1.0, 0.1, self.maxDistance_f * 2.0)

    def getViewMatrix(self, parent) -> np.ndarray:
        ver, hor, _ = self.getWorldDegreeXYZ(parent)

        return mmath.getTranslateMat4(*self.getWorldXYZ(parent), -1).dot(
            mmath.getRotateXYZMat4(hor, 0, 1, 0)
        ).dot(mmath.getRotateXYZMat4(ver, 1, 0, 0))

    def startRender(self) -> None:
        #gl.glDisable(gl.GL_CULL_FACE)
        gl.glViewport(0, 0, self.__shadowW_i, self.__shadowH_i)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.__depthMapFbo)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

    @staticmethod
    def endRender() -> None:
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        #gl.glEnable(gl.GL_CULL_FACE)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    def genShadowMap(self) -> None:
        self.__depthMapFbo = gl.glGenFramebuffers(1)

        self.depthMapTex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.depthMapTex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_DEPTH_COMPONENT, self.__shadowW_i, self.__shadowH_i, 0,
                        gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, None)

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
        # gl.glTexParameterfv(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BORDER_COLOR, (1.0, 1.0, 1.0, 1.0))

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.__depthMapFbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_TEXTURE_2D, self.depthMapTex, 0)
        gl.glDrawBuffer(gl.GL_NONE)
        gl.glReadBuffer(gl.GL_NONE)

        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!")
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
