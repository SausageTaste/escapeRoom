from typing import Tuple

import OpenGL.GL as gl
import numpy as np

from uniloc import UniformLocs
from uniloc_shadow import UniformLocsShadow

from player import Player
from resource_manager import ResourceManager
from camera import Camera
from configs_con import Configs

class RenderingDude:
    def __init__(self, player:Player, resourceManager:ResourceManager, camera:Camera, configs:Configs):
        self.player = player
        self.resourceMan = resourceManager
        self.camera = camera
        self.configs = configs
        
        self.globalEnv = GlobalEmvironment()

        self.__program = self.getProgram()
        self.__programForShadow = self.getProgramForShadow()

        self.uniLoc = UniformLocs(self.__program)
        self.uniLocShadow = UniformLocsShadow(self.__programForShadow)

    def render(self, projectionMat:np.ndarray, viewMat:np.ndarray) -> None:
        gl.glUseProgram(self.__program)

        gl.glUniform1i(self.uniLoc.diffuseMap, 0)

        # in vs
        gl.glUniformMatrix4fv(self.uniLoc.projectionMatrix, 1, gl.GL_FALSE, projectionMat)
        gl.glUniformMatrix4fv(self.uniLoc.viewMatrix, 1, gl.GL_FALSE, viewMat)
        if self.player.flashLightOn_b:
            gl.glUniformMatrix4fv(
                self.uniLoc.flashLightSpaceMatrix, 1, gl.GL_FALSE,
                self.player.flashLight.getViewMatrix(self.player).dot( self.player.flashLight.getPerspectiveMatrix() )
            )

        # in fs
        gl.glUniform3f(self.uniLoc.ambientLight, *self.globalEnv.getAmbient())
        gl.glUniform3f(self.uniLoc.viewPos, *self.camera.getWorldXYZ())

        gl.glUniform1i(self.uniLoc.flashLightOn_i, 1 if self.player.flashLightOn_b else 0)
        if self.player.flashLightOn_b:
            gl.glUniform3f(self.uniLoc.flashLightPos, *self.player.flashLight.getWorldXYZ(self.player))
            gl.glUniform3f(self.uniLoc.flashLightColor, *self.player.flashLight.color_t)
            gl.glUniform3f( self.uniLoc.flashLightDirection, *self.player.flashLight.getLookingVec(self.player).getXYZ() )
            gl.glUniform1f(self.uniLoc.flashLightMaxDist_f, self.player.flashLight.maxDistance_f)
            gl.glUniform1f(self.uniLoc.flashLightCutoff_f, self.player.flashLight.cutoff_f)

            if self.configs.drawFlashLightShadow_b:
                gl.glUniform1i(self.uniLoc.drawFlashLightShadow_i, 1)
                gl.glUniform1i(self.uniLoc.flashLightShadowMap, 1)
                gl.glActiveTexture(gl.GL_TEXTURE1)
                gl.glBindTexture( gl.GL_TEXTURE_2D, self.player.flashLight.depthMapTex )
            else:
                gl.glUniform1i(self.uniLoc.drawFlashLightShadow_i, 0)

        self.resourceMan.renderAll(self.uniLoc)

    def renderShadow(self, winWidth_i, winHeight_i) -> None:
        if self.player.flashLightOn_b and self.configs.drawFlashLightShadow_b:
            gl.glUseProgram(self.__programForShadow)
            self.player.flashLight.startRender()

            gl.glUniformMatrix4fv(
                self.uniLocShadow.lightProjectMat, 1, gl.GL_FALSE, self.player.flashLight.getViewMatrix(self.player).dot(self.player.flashLight.getPerspectiveMatrix())
            )
            self.resourceMan.renderShadow(self.uniLocShadow)

            self.player.flashLight.endRender()

            gl.glViewport(0, 0, winWidth_i, winHeight_i)

    @staticmethod
    def getProgram() -> int:
        vertexShader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        with open("glsl\\renderer_vs.glsl") as file:
            gl.glShaderSource(vertexShader, file.read())
        gl.glCompileShader(vertexShader)
        log_s = gl.glGetShaderInfoLog(vertexShader)
        if log_s:
            raise TypeError(log_s)

        fragmentShader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        with open("glsl\\renderer_fs.glsl") as file:
            gl.glShaderSource(fragmentShader, file.read())
        gl.glCompileShader(fragmentShader)
        log_s = gl.glGetShaderInfoLog(fragmentShader)
        if log_s:
            raise TypeError(log_s)

        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertexShader)
        gl.glAttachShader(program, fragmentShader)
        gl.glLinkProgram(program)

        gl.glDeleteShader(vertexShader)
        gl.glDeleteShader(fragmentShader)

        gl.glUseProgram(program)

        return int( program )

    @staticmethod
    def getProgramForShadow() -> int:
        vertexShader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        with open("glsl\\shadow_vs.glsl") as file:
            gl.glShaderSource(vertexShader, file.read())
        gl.glCompileShader(vertexShader)
        log_s = gl.glGetShaderInfoLog(vertexShader)
        if log_s:
            raise TypeError(log_s)

        fragmentShader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        with open("glsl\\shadow_fs.glsl") as file:
            gl.glShaderSource(fragmentShader, file.read())
        gl.glCompileShader(fragmentShader)
        log_s = gl.glGetShaderInfoLog(fragmentShader)
        if log_s:
            raise TypeError(log_s)

        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertexShader)
        gl.glAttachShader(program, fragmentShader)
        gl.glLinkProgram(program)

        print("Linking Log in Shadow:", gl.glGetProgramiv(program, gl.GL_LINK_STATUS))

        gl.glDeleteShader(vertexShader)
        gl.glDeleteShader(fragmentShader)

        gl.glUseProgram(program)

        return program


class GlobalEmvironment:
    def __init__(self):
        self.__ambient_t = (0.2, 0.2, 0.2)

    def getAmbient(self) -> Tuple[float, float, float]:
        return self.__ambient_t[0], self.__ambient_t[1], self.__ambient_t[2]

    def setAmbient(self, r:float, g:float, b:float):
        self.__ambient_t = ( float(r), float(g), float(b) )