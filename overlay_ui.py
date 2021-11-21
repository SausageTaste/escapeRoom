from typing import Tuple, Optional

import pygame as p
import OpenGL.GL as gl
import numpy as np

import const
import opengl_funcs as of
from uniloc import UniformLocsOverlay
from texture_manager import TextureManager
from curstate import GlobalStates
from language import UiTexts


def getTextMaskMapId(text_s:str, textSize_i:int) -> Tuple[int, float, int, int]:
    if not text_s:
        text_s = " "

    font = p.font.Font(const.DEFAULT_FONT_DIR_s, textSize_i)
    textSurface = font.render(text_s, True, (255, 255, 255, 255), (0, 0, 0, 255))
    image_bytes = p.image.tostring(textSurface, "RGBA", True)
    imgW_i = textSurface.get_width()
    imgH_i = textSurface.get_height()

    imgArray = np.array([x / 255 for x in image_bytes], dtype=np.float32)

    texId = int( gl.glGenTextures(1) )
    if texId is None:
        raise FileNotFoundError("Failed to get texture id.")

    gl.glBindTexture(gl.GL_TEXTURE_2D, texId)
    gl.glTexStorage2D(gl.GL_TEXTURE_2D, 1, gl.GL_RGBA32F, imgW_i, imgH_i)

    gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, imgW_i, imgH_i, gl.GL_RGBA, gl.GL_FLOAT, imgArray)

    texSize_f = imgW_i * imgH_i * 4 * 4 / 1024

    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BASE_LEVEL, 0)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAX_LEVEL, 1)

    #gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    #gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

    gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

    if 1:
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    else:
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST_MIPMAP_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

    return int( texId ), float( texSize_f + texSize_f/3.0 ), imgW_i, imgH_i


class OverlayUiManager:
    def __init__(self, texMan:TextureManager, globalStates:GlobalStates):
        self.texMan = texMan
        self.globalStates = globalStates
        self.winSize_t = ( globalStates.winWidth_i, globalStates.winHeight_i )

        self.uiTexts = UiTexts()

        self.__program_i = of.getProgram(".\\glsl\\overlay_vs.glsl", ".\\glsl\\overlay_fs.glsl")
        self.__uniloc = UniformLocsOverlay(self.__program_i)

        self.consoleWin = ConsoleWindow(self)
        self.darkEffect = OverlayImage( (-1, 1, 1, -1), 1, self.winSize_t, None, None, (0, 0, 0), 0.5 )
        self.menuTexts = MenuTexts(self, self.uiTexts)

        self.frameDisplay = FrameDisplay(self, 10, 5, 15)

        self.blinder = OverlayImage((-1, 1, 1, -1), 1, self.winSize_t, None, None, (0, 0, 0), 0.0)

    def render(self) -> None:
        gl.glUseProgram(self.__program_i)

        gl.glUniform1i(self.__uniloc.diffuseMap, 0)
        gl.glUniform1i(self.__uniloc.maskMap, 1)

        if self.globalStates.showFps_b:
            self.frameDisplay.render(self.__uniloc)

        if self.globalStates.menuPopUp_b:
            self.darkEffect.render(self.__uniloc)
            self.menuTexts.render(self.__uniloc)
        if self.globalStates.consolePopUp_b:
            self.consoleWin.render(self.__uniloc)

        if self.blinder.getBaseMask() != 0.0:
            self.blinder.render(self.__uniloc)

    def resize(self) -> None:
        self.winSize_t = (self.globalStates.winWidth_i, self.globalStates.winHeight_i)

        self.frameDisplay.resize()
        self.consoleWin.resize()
        self.darkEffect.resize(*self.winSize_t)
        self.menuTexts.resize()
        self.blinder.resize(*self.winSize_t)

    def getSelectedButtons(self, xMouse_f:float, yMouse_f:float):
        return self.menuTexts.getMousePointingMenusAndUpdate(xMouse_f, yMouse_f)


class OverlayImage:
    def __init__(self, positionArgs_t:tuple, resizeMode_i:int, winSize_t:tuple,
                 diffuseMap_i:Optional[int], maskMap_i:Optional[int], diffuseColor_t=(1.0, 1.0, 1.0), baseMask_f:float=1.0):
        self.__resizeMode_i = int( resizeMode_i )

        self.__positionArgs_t = positionArgs_t

        self.__xLeftUpper_f = None
        self.__yLeftUpper_f = None
        self.__xRightDown_f = None
        self.__yrightDown_f = None

        self.resize(*winSize_t)

        self.__diffuseMap_i = diffuseMap_i
        self.__maskMap_i = maskMap_i

        self.__diffuseColor_t = ( float(diffuseColor_t[0]), float(diffuseColor_t[1]), float(diffuseColor_t[2]) )
        self.__baseMask_f = float(baseMask_f)

    def __del__(self):
        try:
            gl.glDeleteTextures( self.__maskMap_i )
        except gl.error.GLerror:
            pass

        try:
            gl.glDeleteTextures( self.__diffuseMap_i )
        except gl.error.GLerror:
            pass

    def render(self, uniLoc:UniformLocsOverlay) -> None:
        gl.glUniform2f(uniLoc.leftUpperCoord, self.__xLeftUpper_f, self.__yLeftUpper_f)
        gl.glUniform2f(uniLoc.rightDownCoord, self.__xRightDown_f, self.__yrightDown_f)

        if self.__diffuseMap_i is None:
            gl.glUniform1i(uniLoc.diffuseMap_b, 0)
            gl.glUniform3f(uniLoc.diffuseColor, *self.__diffuseColor_t)
        else:
            gl.glUniform1i(uniLoc.diffuseMap_b, 10)
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.__diffuseMap_i)

        if self.__maskMap_i is None:
            gl.glUniform1i(uniLoc.maskMap_i, 0)
            gl.glUniform1f(uniLoc.baseMask_f, self.__baseMask_f)
        else:
            gl.glUniform1i(uniLoc.maskMap_i, 10)
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.__maskMap_i)

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

    def resize(self, winWidth_i:int, winHeight_i:int) -> None:
        if self.__resizeMode_i == 1:
            self.__resizeAsMode1()
        elif self.__resizeMode_i == 2:
            self.__resizeAsMode2(winWidth_i, winHeight_i)

    def getBoundingCoord(self, winWidth_i:int, winHeight_i:int):
        if self.__resizeMode_i == 2:
            a, b, c, d = self.__positionArgs_t
            return a, b, a+c, b+d
        else:
            raise ValueError

    def setMaskMap(self, maskMapId_i:int) -> None:
        gl.glDeleteTextures( self.__maskMap_i )

        self.__maskMap_i = maskMapId_i

    def setPositionArgs(self, a:Optional[float], b:Optional[float], c:Optional[float], d:Optional[float]) -> None:
        if a is None:
            aNew_f = float( self.__positionArgs_t[0] )
        else:
            aNew_f = float( a )

        if b is None:
            bNew_f = float( self.__positionArgs_t[1] )
        else:
            bNew_f = float( b )

        if c is None:
            cNew_f = float( self.__positionArgs_t[2] )
        else:
            cNew_f = float( c )

        if d is None:
            dNew_f = float( self.__positionArgs_t[3] )
        else:
            dNew_f = float( d )

        self.__positionArgs_t = (aNew_f, bNew_f, cNew_f, dNew_f)

    def setDiffuseColor(self, r, g, b):
        self.__diffuseColor_t = (float(r), float(g), float(b))

    def getBaseMask(self) -> float:
        return self.__baseMask_f

    def setBaseMask(self, value_f:float) -> None:
        self.__baseMask_f = float(value_f)

    def __resizeAsMode1(self) -> None:
        self.__xLeftUpper_f = float( self.__positionArgs_t[0] )
        self.__yLeftUpper_f = float( self.__positionArgs_t[1] )
        self.__xRightDown_f = float( self.__positionArgs_t[2] )
        self.__yrightDown_f = float( self.__positionArgs_t[3] )

    def __resizeAsMode2(self, winWidth_i:int, winHeight_i:int) -> None:
        self.__xLeftUpper_f = float( self.__positionArgs_t[0] / (winWidth_i/2) - 1.0 )
        self.__yLeftUpper_f = -float( self.__positionArgs_t[1] / (winHeight_i/2) - 1.0 )
        self.__xRightDown_f = float( (self.__positionArgs_t[0] + self.__positionArgs_t[2]) / (winWidth_i/2) - 1.0 )
        self.__yrightDown_f = -float( (self.__positionArgs_t[1] + self.__positionArgs_t[3]) / (winHeight_i/2) - 1.0 )


class FrameDisplay:
    def __init__(self, overlayMan:OverlayUiManager, xPos:float, yPos:float, textSize_i:int):
        self.overlayMan = overlayMan
        self.textSize_i = textSize_i

        a = getTextMaskMapId("FPS : ", textSize_i)
        self.frameCounterHead = OverlayImage((xPos, yPos, a[2], a[3]), 2, self.overlayMan.winSize_t, None, a[0])
        b = getTextMaskMapId("450", textSize_i)
        self.frameCounterNumber = OverlayImage((xPos + a[2], yPos, b[2], b[3]), 2, self.overlayMan.winSize_t, None, b[0])

    def render(self, uniloc:UniformLocsOverlay) -> None:
        self.frameCounterHead.render(uniloc)
        self.frameCounterNumber.render(uniloc)

    def resize(self) -> None:
        winWidth_i, winHeight_i = self.overlayMan.winSize_t
        self.frameCounterHead.resize(winWidth_i, winHeight_i)
        self.frameCounterNumber.resize(winWidth_i, winHeight_i)

    def update(self, fps_i:int) -> None:
        b = getTextMaskMapId(str(fps_i), self.textSize_i)
        self.frameCounterNumber.setMaskMap(b[0])
        self.frameCounterNumber.setPositionArgs(None, None, b[2], b[3])
        self.frameCounterNumber.resize(*self.overlayMan.winSize_t)


class WinSizeDisplay:
    def __init__(self, overlayMan:OverlayUiManager, xPos:float, yPos:float, textSize_i:int):
        self.overlayMan = overlayMan
        self.xPos = xPos
        self.yPos = yPos
        self.textSize_i = textSize_i

        a = getTextMaskMapId("Window Size : {} x {}".format(*self.overlayMan.winSize_t), self.textSize_i)
        self.display = OverlayImage((self.xPos, self.yPos, a[2], a[3]), 2, self.overlayMan.winSize_t, None, a[0])

    def render(self, uniloc:UniformLocsOverlay) -> None:
        self.display.render(uniloc)

    def update(self) -> None:
        a = getTextMaskMapId("Window Size : {} x {}".format(*self.overlayMan.winSize_t), self.textSize_i)
        self.display = OverlayImage((self.xPos, self.yPos, a[2], a[3]), 2, self.overlayMan.winSize_t, None, a[0])

    def resize(self) -> None:
        self.update()

        winWidth_i, winHeight_i = self.overlayMan.winSize_t
        self.display.resize(winWidth_i, winHeight_i)


class ConsoleWindow:
    def __init__(self, overlayMan:OverlayUiManager):
        self.overlayMan = overlayMan

        self.currentCommand_s = ""
        self.textSize_i = 20

        self.xPos_f = 10.0
        self.yPos_f = 10.0
        self.xSize_f = 600.0
        self.ySize_f = 600.0

        self.alpha_f = 0.6

        self.box = OverlayImage(
            (10, 10, 500, 600), 2, self.overlayMan.winSize_t, None, None, (0.1, 0.1, 0.1), self.alpha_f
        )

        self.textBox = OverlayImage(
            (15, 10 + self.ySize_f - 25, 500 - 10, 20), 2, self.overlayMan.winSize_t, None, None, (0.15, .15, 0.15),
            self.alpha_f
        )
        self.textInTextBox = OverlayImage(
            (20, 10 + self.ySize_f - 25, 500 - 10, 20), 2, self.overlayMan.winSize_t, None,
            getTextMaskMapId("", self.textSize_i)[0]
        )

        self.logBox = OverlayImage(
            (self.xPos_f + 5.0, self.yPos_f + 5.0, self.xSize_f - 10, self.ySize_f - 35.0), 2, self.overlayMan.winSize_t,
            None, None, (0.15, .15, 0.15), self.alpha_f
        )
        self.logBoxScroll_f = -10.0
        self.logBoxLineSpacing_f = 22.0

        self.logs_l = [
            LogItem("제작자 : 우성민"),
            LogItem("woos8899@gmail.com"),
            LogItem(""),
        ]

        self.__updateLogs()

    def render(self, uniLoc):
        self.box.render(uniLoc)

        self.textBox.render(uniLoc)
        self.textInTextBox.render(uniLoc)

        self.logBox.render(uniLoc)
        for logItem in self.logs_l:
            if not logItem.ready_b:
                continue
            elif logItem.curHeight_f <= 11.0:
                continue
            elif logItem.curHeight_f > self.yPos_f + self.ySize_f - 45.0:
                continue

            logItem.overlayImage.render(uniLoc)

    def resize(self):
        w, h = self.overlayMan.winSize_t

        self.ySize_f = h - 60
        self.xPos_f = w - self.xSize_f - 10.0

        self.box.setPositionArgs(self.xPos_f, self.yPos_f, self.xSize_f, self.ySize_f)
        self.box.resize(w, h)

        self.textBox.setPositionArgs(
            self.xPos_f + 5.0, self.yPos_f + self.ySize_f - 25.0, self.xSize_f - 10.0, 20.0
        )
        self.textBox.resize(w, h)

        self.textInTextBox.setPositionArgs(
            self.xPos_f +10.0, self.yPos_f + self.ySize_f - 25.0, None, 20.0 - 2.0
        )
        self.textInTextBox.resize(w, h)

        self.logBox.setPositionArgs(
            self.xPos_f + 5.0, self.yPos_f + 5.0, self.xSize_f - 10, self.ySize_f - 35.0
        )
        self.logBox.resize(w, h)

        self.__updateLogs()

    def addTextInTextBox(self, text_s:str):
        self.currentCommand_s += str(text_s)
        self.__updateTextInTextBox()

    def eraseOneTextInTextBox(self):
        self.currentCommand_s = self.currentCommand_s[:-1]
        self.__updateTextInTextBox()

    def flushTextInTextBox(self):
        self.currentCommand_s = ""
        self.__updateTextInTextBox()

    def popTextInTextBox(self):
        text_s = self.currentCommand_s
        self.currentCommand_s = ""
        self.__updateTextInTextBox()
        self.appendLogs(">> " + text_s)
        return text_s

    def appendLogs(self, text_s:str):
        self.logs_l.append( LogItem(text_s) )
        self.logBoxScroll_f = -10.0
        self.__updateLogs()

    def addScroll(self, add_f:float):
        self.logBoxScroll_f += add_f
        if self.logBoxScroll_f < -10.0:
            self.logBoxScroll_f = -10.0

        if self.logBoxLineSpacing_f * len(self.logs_l) - self.logBoxScroll_f < 30.0:
            self.logBoxScroll_f = self.logBoxLineSpacing_f * len(self.logs_l) - 30.0

        self.__updateLogs()

    def __updateLogs(self):
        w, h = self.overlayMan.winSize_t

        for x, logItem in enumerate(reversed(self.logs_l)):
            if not logItem.ready_b:
                a = getTextMaskMapId(logItem.text_s, 18)
                logItem.overlayImage = OverlayImage(
                    (0.0, 0.0, 0.0, 0.0), 2,
                    self.overlayMan.winSize_t, None, a[0]
                )
                logItem.textWidth_f = a[2]

                logItem.ready_b = True

            logItem.curHeight_f = self.yPos_f + self.ySize_f - 48.0 - self.logBoxLineSpacing_f*x + self.logBoxScroll_f
            if logItem.curHeight_f > self.yPos_f + self.ySize_f - self.logBoxLineSpacing_f:
                continue
            if logItem.curHeight_f < 10.0:
                break

            logItem.overlayImage.setPositionArgs(
                self.xPos_f+10.0, logItem.curHeight_f, logItem.textWidth_f*0.8, 18.0
            )
            logItem.overlayImage.resize(w, h)

    def __updateTextInTextBox(self):
        a = getTextMaskMapId(self.currentCommand_s, self.textSize_i)
        self.textInTextBox.setMaskMap( a[0] )
        self.textInTextBox.setPositionArgs(
            None, None, a[2] * 0.8, None
        )
        self.textInTextBox.resize(*self.overlayMan.winSize_t)


class LogItem:
    def __init__(self, text_s:str):
        self.ready_b = False

        self.text_s = text_s
        self.overlayImage = None
        self.curHeight_f = None
        self.textWidth_f = None


class MenuTexts:
    def __init__(self, overlayMan:OverlayUiManager, uiTexts:UiTexts):
        self.overlayMan = overlayMan
        self.uiTexts = uiTexts

        texts_t = self.uiTexts.getMenuTexts()

        a = getTextMaskMapId(texts_t[0], 64)
        self.title = OverlayImage( (20, 100, a[2], a[3]), 2, overlayMan.winSize_t, None, a[0] )

        a = getTextMaskMapId(texts_t[1], 35)
        self.resumeGame = OverlayImage((30, 200, a[2], a[3]), 2, overlayMan.winSize_t, None, a[0], (0.5, 0.5, 0.5))
        self.renderResumeGame_b = False

        a = getTextMaskMapId(texts_t[2], 35)
        self.startNewGame = OverlayImage( (30, 250, a[2], a[3]), 2, overlayMan.winSize_t, None, a[0], (0.5, 0.5, 0.5) )

        a = getTextMaskMapId(texts_t[3], 35)
        self.loadGame = OverlayImage((30, 300, a[2], a[3]), 2, overlayMan.winSize_t, None, a[0], (0.5, 0.5, 0.5))

        a = getTextMaskMapId(texts_t[4], 35)
        self.settings = OverlayImage((30, 350, a[2], a[3]), 2, overlayMan.winSize_t, None, a[0], (0.5, 0.5, 0.5))

        a = getTextMaskMapId(texts_t[5], 35)
        self.exit = OverlayImage( (30, 400, a[2], a[3]), 2, overlayMan.winSize_t, None, a[0], (0.5, 0.5, 0.5) )

    def render(self, uniLoc):
        self.title.render(uniLoc)

        if self.renderResumeGame_b:
            self.resumeGame.render(uniLoc)
        self.startNewGame.render(uniLoc)
        self.loadGame.render(uniLoc)
        self.settings.render(uniLoc)
        self.exit.render(uniLoc)

    def resize(self):
        assert len(self.overlayMan.winSize_t)

        self.title.resize(*self.overlayMan.winSize_t)

        self.resumeGame.resize(*self.overlayMan.winSize_t)
        self.startNewGame.resize(*self.overlayMan.winSize_t)
        self.loadGame.resize(*self.overlayMan.winSize_t)
        self.settings.resize(*self.overlayMan.winSize_t)
        self.exit.resize(*self.overlayMan.winSize_t)

    def getMousePointingMenusAndUpdate(self, xMouse_f:float, yMouse_f:float):
        a, b, c, d = self.startNewGame.getBoundingCoord( *self.overlayMan.winSize_t )
        if self.__checkMouseInsideBox((a, b), (c, d), xMouse_f, yMouse_f):
            self.startNewGame.setDiffuseColor(1.0, 1.0, 1.0)
            startNewGameMouse_b = True
        else:
            self.startNewGame.setDiffuseColor(0.5, 0.5, 0.5)
            startNewGameMouse_b = False

        a, b, c, d = self.loadGame.getBoundingCoord(*self.overlayMan.winSize_t)
        if self.__checkMouseInsideBox((a, b), (c, d), xMouse_f, yMouse_f):
            self.loadGame.setDiffuseColor(1.0, 1.0, 1.0)
            loadGameMouse_b = True
        else:
            self.loadGame.setDiffuseColor(0.5, 0.5, 0.5)
            loadGameMouse_b = False

        a, b, c, d = self.settings.getBoundingCoord(*self.overlayMan.winSize_t)
        if self.__checkMouseInsideBox((a, b), (c, d), xMouse_f, yMouse_f):
            self.settings.setDiffuseColor(1.0, 1.0, 1.0)
            settingsMouse_b = True
        else:
            self.settings.setDiffuseColor(0.5, 0.5, 0.5)
            settingsMouse_b = False

        a, b, c, d = self.exit.getBoundingCoord(*self.overlayMan.winSize_t)
        if self.__checkMouseInsideBox((a, b), (c, d), xMouse_f, yMouse_f):
            self.exit.setDiffuseColor(1.0, 1.0, 1.0)
            exitMouse_b = True
        else:
            self.exit.setDiffuseColor(0.5, 0.5, 0.5)
            exitMouse_b = False

        a, b, c, d = self.resumeGame.getBoundingCoord(*self.overlayMan.winSize_t)
        if self.renderResumeGame_b and self.__checkMouseInsideBox((a, b), (c, d), xMouse_f, yMouse_f):
            self.resumeGame.setDiffuseColor(1.0, 1.0, 1.0)
            resumeGameMouse_b = True
        else:
            self.resumeGame.setDiffuseColor(0.5, 0.5, 0.5)
            resumeGameMouse_b = False

        return startNewGameMouse_b, loadGameMouse_b, settingsMouse_b, exitMouse_b, resumeGameMouse_b

    @staticmethod
    def __checkMouseInsideBox(boxMin_t, boxMax_t, xMouse_f, yMouse_f):
        if xMouse_f < boxMin_t[0]:
            return False
        elif xMouse_f > boxMax_t[0]:
            return False
        elif yMouse_f < boxMin_t[1]:
            return False
        elif yMouse_f > boxMax_t[1]:
            return False
        else:
            return True
