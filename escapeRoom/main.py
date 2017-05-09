import os
import sys
import traceback
import multiprocessing
from time import sleep

import pygame as p
import OpenGL.GL as gl
import pygame.locals as pl

import actor
import mmath as mm
import text_funcs as tf
from camera import Camera
from player import Player
from configs_con import Configs
from mpygame import FrameManager
from curstate import GlobalStates
from gameLogic import LogicalDude
from rendering_dude import RenderingDude
from resource_manager import ResourceManager


class Controller:
    def __init__(self, mainLoop:"MainLoop", target:Player=None):
        self.mainLoop = mainLoop
        self.globalStates = self.mainLoop.globalStates
        self.target = target
        self.configs = mainLoop.configs
        self.commander = mainLoop.commander

        self.mouseControl_b = True
        self.lastMousePos_t = p.mouse.get_pos()
        self.enableMouseControl(False)

        p.joystick.init()
        self.joysticks_l = [p.joystick.Joystick(x) for x in range(p.joystick.get_count())]
        for jo in self.joysticks_l:
            jo.init()
        self.joystick_b = True if len(self.joysticks_l) else False

    def update(self) -> None:
        openedConsole_b = False
        if self.globalStates.titleScreen_b:
            for event in p.event.get():
                if event.type == pl.QUIT:
                    self.mainLoop.commandQueue_l.append("sys_exit")
                elif event.type == pl.VIDEORESIZE:
                    self.globalStates.winWidth_i = event.dict['w']
                    self.globalStates.winHeight_i = event.dict['h']
                    self.mainLoop.onResize()
                elif event.type == pl.KEYDOWN:
                    console = self.mainLoop.console
                    if event.key == pl.K_BACKQUOTE:
                        if self.globalStates.consolePopUp_b:
                            self.returnToGame()
                        else:
                            self.globalStates.consolePopUp_b = True
                            self.globalStates.menuPopUp_b = True
                            self.enableMouseControl(False)
                            openedConsole_b = True
                    if self.globalStates.consolePopUp_b:
                        if event.key == pl.K_SPACE:
                            console.addTextInTextBox(" ")
                        elif event.key == pl.K_BACKSPACE:
                            console.eraseOneTextInTextBox()
                        elif event.key == pl.K_RETURN:
                            self.mainLoop.commandQueue_l.append( console.popTextInTextBox() )
                        else:
                            try:
                                console.addTextInTextBox(event.unicode)
                            except:
                                pass
                elif event.type == pl.MOUSEMOTION:
                    self.mainLoop.resourceManager.overlayUiMan.getSelectedButtons(*p.mouse.get_pos())
                elif event.type == pl.MOUSEBUTTONDOWN:
                    if event.button == 1:  # left click
                        selectedButtons_t = self.mainLoop.resourceManager.overlayUiMan.getSelectedButtons(*p.mouse.get_pos())
                        if selectedButtons_t[0]:
                            self.mainLoop.commandQueue_l.append("sys_start_new_game")
                        elif selectedButtons_t[1]:
                            self.mainLoop.commandQueue_l.append("win_load_game")
                        elif selectedButtons_t[2]:
                            self.mainLoop.commandQueue_l.append("win_settings")
                        elif selectedButtons_t[3]:
                            self.mainLoop.commandQueue_l.append("sys_exit")
                    if self.globalStates.consolePopUp_b:
                        a, b, c, d = self.mainLoop.console.logBox.getBoundingCoord(
                            self.globalStates.winWidth_i, self.globalStates.winHeight_i
                        )
                        if not self.checkMouseInsideBox((a, b), (c, d)):
                            continue

                        if event.button == 4:  # scroll up
                            self.mainLoop.console.addScroll(20.0)
                        elif event.button == 5:  # scroll down
                            self.mainLoop.console.addScroll(-20.0)
        elif self.globalStates.menuPopUp_b:
            for event in p.event.get():
                if event.type == pl.QUIT:
                    self.mainLoop.commandQueue_l.append("sys_exit")
                elif event.type == pl.VIDEORESIZE:
                    self.globalStates.winWidth_i = event.dict['w']
                    self.globalStates.winHeight_i = event.dict['h']
                    self.mainLoop.onResize()
                elif event.type == pl.KEYDOWN:
                    console = self.mainLoop.console
                    if event.key == pl.K_ESCAPE:
                        self.returnToGame()
                    elif event.key == pl.K_BACKQUOTE:
                        if self.globalStates.consolePopUp_b:
                            self.returnToGame()
                        else:
                            self.globalStates.consolePopUp_b = True
                            self.globalStates.menuPopUp_b = True
                            self.enableMouseControl(False)
                            openedConsole_b = True
                    if self.globalStates.consolePopUp_b:
                        if event.key == pl.K_SPACE:
                            console.addTextInTextBox(" ")
                        elif event.key == pl.K_BACKSPACE:
                            console.eraseOneTextInTextBox()
                        elif event.key == pl.K_RETURN:
                            self.mainLoop.commandQueue_l.append( console.popTextInTextBox() )
                        else:
                            try:
                                console.addTextInTextBox(event.unicode)
                            except:
                                pass
                elif event.type == pl.MOUSEMOTION:
                    self.mainLoop.resourceManager.overlayUiMan.getSelectedButtons(*p.mouse.get_pos())
                elif event.type == pl.MOUSEBUTTONDOWN:
                    if event.button == 1:  # left click
                        selectedButtons_t = self.mainLoop.resourceManager.overlayUiMan.getSelectedButtons(*p.mouse.get_pos())
                        if selectedButtons_t[0]:
                            self.mainLoop.commandQueue_l.append("sys_start_new_game")
                        elif selectedButtons_t[1]:
                            self.mainLoop.commandQueue_l.append("win_load_game")
                        elif selectedButtons_t[2]:
                            self.mainLoop.commandQueue_l.append("win_settings")
                        elif selectedButtons_t[3]:
                            self.mainLoop.commandQueue_l.append("sys_exit")
                        elif selectedButtons_t[4]:
                            self.returnToGame()
                    if self.globalStates.consolePopUp_b:
                        a, b, c, d = self.mainLoop.console.logBox.getBoundingCoord(
                            self.globalStates.winWidth_i, self.globalStates.winHeight_i
                        )
                        if not self.checkMouseInsideBox((a, b), (c, d)):
                            continue

                        if event.button == 4:  # scroll up
                            self.mainLoop.console.addScroll(20.0)
                        elif event.button == 5:  # scroll down
                            self.mainLoop.console.addScroll(-20.0)
        else:
            for event in p.event.get():
                if event.type == pl.QUIT:
                    self.mainLoop.commandQueue_l.append("sys_exit")
                elif event.type == pl.VIDEORESIZE:
                    self.globalStates.winWidth_i = event.dict['w']
                    self.globalStates.winHeight_i = event.dict['h']
                    self.mainLoop.onResize()
                elif event.type == pl.KEYDOWN:
                    if event.key == pl.K_ESCAPE:
                        self.globalStates.menuPopUp_b = True
                        self.enableMouseControl(False)
                    elif event.key == pl.K_f:
                        if self.target.flashLightOn_b:
                            self.target.flashLightOn_b = False
                        else:
                            self.target.flashLightOn_b = True
                    elif event.key == pl.K_e:
                        self.mainLoop.commandQueue_l += self.mainLoop.player.nearbyTriggers
                        self.mainLoop.player.nearbyTriggers = []
                    elif event.key == pl.K_BACKQUOTE:
                        self.globalStates.consolePopUp_b = True
                        self.globalStates.menuPopUp_b = True
                        self.enableMouseControl(False)
                        openedConsole_b = True

        if openedConsole_b:
            self.mainLoop.console.flushTextInTextBox()

        if self.target is None:
            return
        elif self.globalStates.menuPopUp_b:
            return
        elif self.globalStates.freezeLogic_b:
            return

        fDelta_f = self.mainLoop.fMan.getFrameDelta()
        pressed_t = p.key.get_pressed()

        x = 0.0
        z = 0.0
        if pressed_t[pl.K_w]:
            z -= 1.0
        if pressed_t[pl.K_a]:
            x -= 1.0
        if pressed_t[pl.K_s]:
            z += 1.0
        if pressed_t[pl.K_d]:
            x += 1.0
        directionVec4 = mm.Vec4(x, 0, z).normalize().transform(mm.getRotateYMat4(-self.target.getAngleY().getDegree()))
        self.target.giveHorizontalMomentum(directionVec4.getX(), directionVec4.getZ())

        if pressed_t[pl.K_RIGHT]:
            self.target.getAngleY().addDegree(-fDelta_f * self.configs.keyboardLookSensitivity_f * 5)
        if pressed_t[pl.K_LEFT]:
            self.target.getAngleY().addDegree(fDelta_f * self.configs.keyboardLookSensitivity_f * 5)
        if pressed_t[pl.K_UP]:
            self.target.getAngleX().addDegree(fDelta_f * self.configs.keyboardLookSensitivity_f * 5)
        if pressed_t[pl.K_DOWN]:
            self.target.getAngleX().addDegree(-fDelta_f * self.configs.keyboardLookSensitivity_f * 5)
        if pressed_t[pl.K_SPACE]:
            self.target.startJumping()

        if self.mouseControl_b:
            self.updateMouse()
        if self.joystick_b:
            self.updateJoystick(fDelta_f)

        self.target.validateValuesForCamera()

    def enableMouseControl(self, really_b:bool) -> None:

        if really_b:
            self.lastMousePos_t = p.mouse.get_pos()
            configs = self.mainLoop.configs
            p.mouse.set_pos(configs.initScreenSizeWidth_i//2, configs.initScreenSizeHeight_i//2)

            self.mouseControl_b = True
            p.event.set_grab(True)
            p.mouse.set_visible(False)
        else:
            self.mouseControl_b = False
            p.event.set_grab(False)
            p.mouse.set_visible(True)

            p.mouse.set_pos(*self.lastMousePos_t)

        p.mouse.get_rel()
        p.mouse.get_rel()

    def updateMouse(self) -> None:
        a, b = p.mouse.get_rel()
        if abs(a) == 1:
            a = 0
        if abs(b) == 1:
            b = 0

        a = a / self.mainLoop.globalStates.winWidth_i * -5.0 * self.configs.mouseSensitivity_f
        b = b / self.mainLoop.globalStates.winHeight_i * -5.0 * self.configs.mouseSensitivity_f

        if a or b:
            self.target.getAngleY().addDegree(a)
            self.target.getAngleX().addDegree(b)

    def updateJoystick(self, fDelta_f:float) -> None:
        for jo in self.joysticks_l:
            a = jo.get_axis(0)
            b = jo.get_axis(1)
            if abs(a) < 0.1:
                a = 0.0
            if abs(b) < 0.1:
                b = 0.0
            self.target.moveAround(mm.Vec4(a, 0, b),fDelta_f*3)

            a = jo.get_axis(3)
            b = jo.get_axis(4)
            if abs(a) < 0.1:
                a = 0.0
            if abs(b) < 0.1:
                b = 0.0
            self.target.getAngleY().addDegree(-fDelta_f*b*100)
            self.target.getAngleX().addDegree(-fDelta_f*a*100)

    def returnToGame(self):
        self.globalStates.menuPopUp_b = False
        self.globalStates.consolePopUp_b = False
        self.enableMouseControl(True)

    @staticmethod
    def checkMouseInsideBox(boxMin_t, boxMax_t):
        xMouse_f, yMouse_f = p.mouse.get_pos()
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


class Commander:
    def __init__(self, mainLoop:"MainLoop"):
        self.mainLoop = mainLoop

        self.commandQueue_l = mainLoop.commandQueue_l

        self.commandTable_d = {
            "help":                 self.help,

            "sys_exit":             self.sys_exit,
            "sys_start_new_game":   self.sys_start_new_game,
            "sys_freeze":           self.sys_freeze,

            "win_load_game":        self.win_load_game,
            "win_settings":         self.win_settings,

            "level_del":            self.level_del,
            "level_load":           self.level_load,

            "obj_set_pos":          self.obj_setpos,
            "obj_del":              self.obj_del,
            "obj_set_scale":              self.obj_set_scale,

            "conf_flash_shadow":    self.conf_flash_shadow,

            "ui_show_fps":          self.ui_showfps,
            "ui_set_blinder":       self.ui_set_blinder,

            "print_res":            self.print_res,

            "gr_set_ambient":       self.gr_set_ambient,
            "gr_get_ambient":       self.gr_get_ambient,

            "pl_set_pos":           self.pl_set_pos,
            "pl_get_pos":           self.pl_get_pos,
            "pl_set_degree":        self.pl_set_degree,
            "pl_get_degree":        self.pl_get_degree,
            "pl_toggle_flashlight": self.pl_toggle_flashlight,
        }

    def update(self) -> None:
        for x in range(len(self.commandQueue_l) -1, -1, -1):
            command_s = self.commandQueue_l[x]
            del self.commandQueue_l[x]

            if not command_s:
                continue
            self.parseTextCommand(command_s)

    def parseTextCommand(self, command_s:str) -> None:
        command_l = command_s.split()

        try:
            func = self.commandTable_d[command_l[0]]
        except KeyError:
            self.mainLoop.console.appendLogs("Invalid command: '{}'".format(command_l[0]))
        else:
            try:
                func(command_l)
            except SystemExit:
                sys.exit(0)
            except:
                traceback.print_exc()
                print("Failed to execute a command: '{}'".format(command_l[0]))
                self.mainLoop.console.appendLogs("Failed to execute a command: '{}'".format(command_l[0]))
            else:
                print("Command:", command_l)

    def getMostSimilarCommand(self, wrongCommand_s:str):
        mostScore_i = 0
        mostSimilarCommand_s = None

        for aCommand_s in self.commandTable_d.keys():
            score_i = tf.getTextSimilarity(wrongCommand_s, aCommand_s)
            if score_i > mostScore_i:
                mostScore_i = score_i
                mostSimilarCommand_s = aCommand_s

        return mostSimilarCommand_s

    def __notImplemented(self, command_l:list):
        self.mainLoop.console.appendLogs( "Not implemented command: '{}'".format(command_l[0]) )

    # Commands

    def help(self, command_l: list):
        if len(command_l) == 1:
            self.mainLoop.console.appendLogs(
                "This command finds a valid command that is similar to following string."
            )
        else:
            result = self.getMostSimilarCommand(" ".join(command_l[1:]))
            if result is None:
                self.mainLoop.console.appendLogs("Can't find any similar command.")
            else:
                self.mainLoop.console.appendLogs("Maybe you were looking for: '{}'".format(result))

    def sys_exit(self, _:list):
        self.mainLoop.terminate()
        sys.exit(0)

    def sys_start_new_game(self, _:list):
        self.ui_set_blinder([None, 1.0])
        self.sys_freeze([None, 1])

        self.level_del_all([None])
        self.level_load([None, "c01_01"])
        self.pl_set_pos([None, 0, 0, 0])
        self.pl_set_degree([None, 0, 0, 0])

        self.mainLoop.globalStates.consolePopUp_b = False
        self.mainLoop.globalStates.menuPopUp_b = False
        self.mainLoop.globalStates.titleScreen_b = False
        self.mainLoop.controller.enableMouseControl(True)
        self.mainLoop.resourceManager.overlayUiMan.menuTexts.renderResumeGame_b = True

    def sys_freeze(self, command_l:list):
        if int(command_l[1]):
            self.mainLoop.globalStates.freezeLogic_b = True
        else:
            self.mainLoop.globalStates.freezeLogic_b = False

    def win_load_game(self, command_l:list):
        self.__notImplemented(command_l)

    def win_settings(self, command_l:list):
        self.__notImplemented(command_l)

    def level_del(self, command_l:list):
        self.mainLoop.resourceManager.deleteLevel(command_l[1])

    def level_del_all(self, _:list):
        self.mainLoop.resourceManager.deleteAllLevels()

    def level_load(self, command_l:list):
        try:
            self.mainLoop.resourceManager.requestLevelLoad(command_l[1])
        except FileNotFoundError:
            self.mainLoop.console.appendLogs("Level not found: '{}'".format(command_l[1]))

    def obj_setpos(self, command_l:list):
        obj = self.mainLoop.resourceManager.findObjectInLevelByName(command_l[1], command_l[2])
        if obj is None:
            self.mainLoop.console.appendLogs(
                "Failed to find an object '{}' in level '{}'".format(command_l[1], command_l[2])
            )
        else:
            try:
                obj.setPosX(float(command_l[3]))
                obj.setPosY(float(command_l[4]))
                obj.setPosZ(float(command_l[5]))
            except actor.InvalidForStaticActor:
                self.mainLoop.console.appendLogs(
                    "The object '{}' in level '{}' is static.".format(command_l[1], command_l[2])
                )
            else:
                self.mainLoop.console.appendLogs(
                    "The object '{}' in level '{}' has been move to position {}, {}, {}".format(
                        command_l[1], command_l[2], float(command_l[3]), float(command_l[4]),
                        float(command_l[5])
                    )
                )

    def obj_set_scale(self, command_l:list):
        obj = self.mainLoop.resourceManager.findObjectInLevelByName(command_l[1], command_l[2])
        if obj is None:
            self.mainLoop.console.appendLogs(
                "Failed to find an object '{}' in level '{}'".format(command_l[1], command_l[2])
            )
        else:
            try:
                obj.setScaleXYZ(command_l[3], command_l[4], command_l[5])
            except actor.InvalidForStaticActor:
                self.mainLoop.console.appendLogs(
                    "The object '{}' in level '{}' is static.".format(command_l[1], command_l[2])
                )
            else:
                self.mainLoop.console.appendLogs(
                    "The object '{}' in level '{}' has been resized to {}, {}, {}".format(
                        command_l[1], command_l[2], float(command_l[3]), float(command_l[4]),
                        float(command_l[5])
                    )
                )

    def obj_del(self, command_l:list):
        self.mainLoop.resourceManager.deleteAnObject(command_l[1], command_l[2])

    def conf_flash_shadow(self, command_l:list):
        self.mainLoop.configs.drawFlashLightShadow_b = bool(int(command_l[1]))

    def ui_showfps(self, command_l:list):
        self.mainLoop.globalStates.showFps_b = bool(int(command_l[1]))

    def ui_set_blinder(self, command_l:list):
        self.mainLoop.resourceManager.overlayUiMan.blinder.setBaseMask(command_l[1])

    def print_res(self, _:list):
        self.mainLoop.console.appendLogs(
            "width: {}, height: {}".format(self.mainLoop.globalStates.winWidth_i,
                                           self.mainLoop.globalStates.winHeight_i)
        )

    def gr_set_ambient(self, command_l:list):
        self.mainLoop.renderDude.globalEnv.setAmbient(float(command_l[1]), float(command_l[2]), float(command_l[3]))

    def gr_get_ambient(self, _:list):
        self.mainLoop.console.appendLogs("Ambient: {}, {}, {}".format(*self.mainLoop.renderDude.globalEnv.getAmbient()))

    def pl_set_pos(self, command_l:list):
        self.mainLoop.player.setPosX( command_l[1] )
        self.mainLoop.player.setPosY( command_l[2] )
        self.mainLoop.player.setPosZ( command_l[3] )

    def pl_get_pos(self, _:list):
        self.mainLoop.console.appendLogs("Player position: {:f}, {:f}, {:f}".format(*self.mainLoop.player.getPosXYZ()))

    def pl_set_degree(self, command_l:list):
        xAngle, yAngle, zAngle = self.mainLoop.player.getAngleXYZ()

        try:
            xAngle.setDegree(command_l[1])
            yAngle.setDegree(command_l[2])
            zAngle.setDegree(command_l[3])
        except:
            traceback.print_exc()

    def pl_get_degree(self, _:list):
        xAngle, yAngle, zAngle = self.mainLoop.player.getAngleXYZ()
        self.mainLoop.console.appendLogs("Player looking degree: {}, {}, {}".format(
            xAngle.getDegree(), yAngle.getDegree(), zAngle.getDegree()
        ))

    def pl_toggle_flashlight(self, command_l: list):
        if int(command_l[1]):
            self.mainLoop.player.flashLightOn_b = True
        else:
            self.mainLoop.player.flashLightOn_b = False


class MainLoop:
    def __init__(self):
        try:
            os.environ['SDL_VIDEO_WINDOW_POS'] = str(44) + "," + str(44)

            self.commandQueue_l = []
            self.projectionMatrix = None

            self.configs = Configs()
            self.globalStates = GlobalStates()
            self.commander = Commander(self)

            self.globalStates.winWidth_i = self.configs.initScreenSizeWidth_i
            self.globalStates.winHeight_i = self.configs.initScreenSizeHeight_i

            p.init()
            winSize_t = ( self.globalStates.winWidth_i, self.globalStates.winHeight_i )
            if self.configs.fullScreen_b:
                p.display.set_mode(winSize_t, pl.DOUBLEBUF | pl.OPENGL | pl.FULLSCREEN)
            else:
                p.display.set_mode(winSize_t, pl.DOUBLEBUF | pl.OPENGL | pl.RESIZABLE)

            self.player = Player()
            self.camera = Camera("main_camera", self.player, (0.0, 1.6, 0.0))
            self.controller = Controller(self, self.player)

            self.resourceManager = ResourceManager(self.globalStates)
            self.resourceManager.runProcesses()
            self.resourceManager.requestLevelLoad("entry", 5.0)

            self.console = self.resourceManager.overlayUiMan.consoleWin

            self.fMan = FrameManager( False, self.resourceManager.overlayUiMan.frameDisplay.update, 0 )

            self.renderDude = RenderingDude(self.player, self.resourceManager, self.camera, self.configs)
            self.logicalDude = LogicalDude(self.resourceManager, self.player, self.commandQueue_l, self.globalStates)

            self.globalStates.menuPopUp_b = True
            self.controller.enableMouseControl(False)

            self.initGL()
        except:
            self.terminate()
            raise

    @staticmethod
    def initGL():
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def terminate(self) -> None:
        try:
            self.resourceManager.terminate()
        except:
            pass

        p.quit()

    def run(self) -> None:
        while True:
            self.fMan.update()

            ######## User input ########

            self.controller.update()

            ######## Game logic ########

            self.logicalDude.update()

            self.commander.update()

            ######## Resource ########

            self.resourceManager.update()

            ######## Render ########

            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            gl.glClearBufferfv(gl.GL_COLOR, 0, (0.0, 0.0, 0.0))

            gl.glEnable(gl.GL_CULL_FACE)
            gl.glEnable(gl.GL_DEPTH_TEST)

            self.renderDude.renderShadow(self.globalStates.winWidth_i, self.globalStates.winHeight_i)

            self.renderDude.render( self.projectionMatrix, self.camera.getViewMatrix() )

            p.display.flip()

    def onResize(self) -> None:
        w = self.globalStates.winWidth_i
        h = self.globalStates.winHeight_i

        gl.glViewport(0, 0, w, h)
        self.projectionMatrix = mm.getPerspectiveMat4(90.0, w / h, 0.1, 100.0)

        self.resourceManager.resize()


def main():
    try:
        mainLoop = MainLoop()
    except:
        print('\nSERIOUS ERROR during initializing!!')
        traceback.print_exc()
        sleep(1)
        input("Press any key to continue...")
        sys.exit(-1)
    else:
        try:
            mainLoop.run()
        except SystemExit:  # When the app is closed my clicking close button.
            mainLoop.terminate()
            sys.exit(0)
        except:  # I want to see what exception crashed my god damn app.
            mainLoop.terminate()
            print('\nSERIOUS ERROR during run time!!')
            traceback.print_exc()
            sleep(1)
            input("Press any key to continue...")
            sys.exit(-1)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
