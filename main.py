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
            "level_del_all":        self.level_del_all,
            "level_load":           self.level_load,

            "obj_set_pos":          self.obj_setpos,
            "obj_del":              self.obj_del,
            "obj_set_scale":        self.obj_set_scale,

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

    ######## Commands ########

    def help(self, command_l: list):
        """
        "help [arg1] [arg2] [arg3] ... [arg4444]"
        
        인자로 주어진 문자열들과 가장 유사한 명령어를 출력합니다.
        명령어가 구체적으로 어떤 문자열인지 기억이 잘 안 날 때 사용하시면 됩니다.
        
        예) "help flash shadow" -> 인게임 콘솔에 "conf_flash_shadow" 출력.
        """
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
        """
        "sys_exit"
        
        사용 중인 자원을 모두 반환하고 멀티프로세스들을 모두 종료한 뒤 프로그램을 완전히 종료합니다.
        """
        self.mainLoop.terminate()
        sys.exit(0)

    def sys_start_new_game(self, _:list):
        """
        "sys_start_new_game"
        
        메뉴 화면에서 '처음부터 시작' 버튼을 누르는 것과 동일한 일을 합니다.
        """
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
        """
        "sys_freeze (0 or 1: int)"
        
        인자로 0 외의 숫자가 주어지면 사용자의 조작을 막으며 0이 주어지면 풀립니다.
        """
        if int(command_l[1]):
            self.mainLoop.globalStates.freezeLogic_b = True
        else:
            self.mainLoop.globalStates.freezeLogic_b = False

    def win_load_game(self, command_l:list):
        """
        "win_load_game"
        
        로딩은 아직 구현되지 않았습니다.
        """
        self.__notImplemented(command_l)

    def win_settings(self, command_l:list):
        """
        "win_settings"
        
        설정창을 아직 구현되지 않았습니다.
        """
        self.__notImplemented(command_l)

    def level_del(self, command_l:list):
        """
        "level_del (level name)"
        
        인자로 주어진 이름을 갖고 있는 레벨을 삭제합니다.
        레벨은 오브젝트들을 포함하는 상위 객체이며, 이것이 지워지면 포함된 오브젝트들도 모두 지워집니다.
        
        예) "level_del c01_02" -> 긴 통로를 삭제합니다.
        """
        self.mainLoop.resourceManager.deleteLevel(command_l[1])

    def level_del_all(self, _:list):
        """
        "level_del_all"
        
        모든 레벨을 삭제합니다.
        이 명령어를 쓰고 싶은 마음이 전혀 안 들어야 정상입니다.
        삐빅! 비정상입니다.
        """
        self.mainLoop.resourceManager.deleteAllLevels()

    def level_load(self, command_l:list):
        """
        "level_load (level name)"
        
        인자로 주어진 이름을 가진 레벨 파일을 불러 옵니다.
        레벨 파일들은 escapeRoom\\assets\\levels 폴더 안에 있습니다.
        인자로 이름을 줄 때, 확장자 .smll은 떼야 합니다.
        
        예) "level_load entry" -> 초기 시작 화면에 배경으로 등장하는 긴 통로 레벨을 불러옵니다.
        """
        try:
            self.mainLoop.resourceManager.requestLevelLoad(command_l[1])
        except FileNotFoundError:
            self.mainLoop.console.appendLogs("Level not found: '{}'".format(command_l[1]))

    def obj_setpos(self, command_l:list):
        """
        "obj_set_pos (level name) (object instance name) (x pos: float) (y pos: float) (z pos: float)"
        함수명과 명령어가 같이 않으므로 주의!
        
        (level name)이라는 이름을 가진 레벨 안의 (object instance name)라는 이름을 가진 오브젝트를
        (x pos: float) (y pos: float) (z pos: float) 위치로 이동합니다.
        
        예) "obj_set_pos c01_01 seoul -20 1 0" -> 서울 오브젝트를 옆 통로로 옮깁니다.
        """
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
        """
        "obj_set_scale (level name) (object instance name) (x scale: float) (y scale: float) (z scale: float)"
        
        obj_set_pos와 사용법은 비슷합니다.
        다만 이 명령어는 크기를 조절합니다.
        
        예) "obj_set_scale c01_01 seoul 0.5 3 0.5" -> 서울 오브젝트를 좁고 두껍게 만듧니다. 케잌 먹고 싶어지는 부분.
        """
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
        """
        "obj_del (level name) (object instance name)"
        
        (level name) 레벨 안에 있는 (object instance name) 오브젝트를 삭제합니다.
        만약 마지막 남은 인스턴스인 경우 해당 오브젝트의 메쉬는 메모리에서 반환됩니다.
        
        "obj_del c01_01 seoul" -> 서울 오브젝트를 제거하고 메모리를 반환합니다.
        """
        self.mainLoop.resourceManager.deleteAnObject(command_l[1], command_l[2])

    def conf_flash_shadow(self, command_l:list):
        """
        "conf_flash_shadow (0 or 1: int)"
        
        손전등의 그림자를 켜고 끌 수 있습니다.
        제 발적화 덕분에 손전등 그림자가 fps를 많이 잡아먹기 때문에 끌 수 있도록 만들었습니다.
        
        "conf_flash_shadow 0" -> 손전등의 그림자를 끄고 fps를 개선합니다.
        """
        self.mainLoop.configs.drawFlashLightShadow_b = bool(int(command_l[1]))

    def ui_showfps(self, command_l:list):
        """
        "ui_show_fps (0 or 1: int)"
        메소드명과 명령어 이름이 다르므로 주의!

        화면 좌측 상단에 표시되는 fps 표시기를 켜고 끌 수 있습니다.

        "ui_show_fps 0" -> fps 표시기를 끕니다.
        """
        self.mainLoop.globalStates.showFps_b = bool(int(command_l[1]))

    def ui_set_blinder(self, command_l:list):
        """
        "ui_set_blinder (0 or 1: int)"
        
        화면 전체를 검은 색으로 칠합니다.
        쓰지 마세요. 콘솔창도 가려버립니다.
        이 명령어는 화면 전환 등에 쓰이기 위해 만들어졌습니다.
        
        "ui_set_blinder 1" -> 화면 전체를 검은색으로 덮습니다.
        """
        self.mainLoop.resourceManager.overlayUiMan.blinder.setBaseMask(command_l[1])

    def print_res(self, _:list):
        """
        "print_res"
        
        인게임 콘솔에 프로그램의 현재 해상도를 출력합니다.
        """
        self.mainLoop.console.appendLogs(
            "width: {}, height: {}".format(self.mainLoop.globalStates.winWidth_i,
                                           self.mainLoop.globalStates.winHeight_i)
        )

    def gr_set_ambient(self, command_l:list):
        """
        "gr_set_ambient (r value: float) (g value: float) (b value: float)"
        
        엠비언트 색상 RGB를 설정합니다.
        엠비언트 색상은 물체가 아무런 빛을 받지 않았을 경우 기본적으로 받는 빛의 색깔입니다.
        기본값은 0.0, 0.0, 0.0으로, 빛을 전혀 받지 않으면 전혀 보이지 않습니다.
        1.0, 1.0, 1.0으로 설정된 경우 빛을 전혀 받지 않은 물체의 밝기는 텍스처 이미지의 밝기와 완전히 동일해집니다.
        
        예) "gr_set_ambient 0.2 0.2 0.2" -> 전체적인 밝기를 약간 높입니다.
        """
        self.mainLoop.renderDude.globalEnv.setAmbient(float(command_l[1]), float(command_l[2]), float(command_l[3]))

    def gr_get_ambient(self, _:list):
        """
        "gr_get_ambient"
        
        현재 엠비언트 색상을 인게임 콘솔에 출력합니다.
        """
        self.mainLoop.console.appendLogs("Ambient: {}, {}, {}".format(*self.mainLoop.renderDude.globalEnv.getAmbient()))

    def pl_set_pos(self, command_l:list):
        """
        "pl_set_pos (x pos: float) (y pos: float) (z pos: float)"
        
        플레이어의 위치를 설정합니다.
        레벨 밖으로 떨어진 경우 위치를 0 0 0으로 설정해 주시면 원래 자리로 돌아올 수 있습니다.
        
        "pl_set_pos 0 0 0" -> 월드의 중심으로 텔레포트 합니다.
        """
        self.mainLoop.player.setPosX( command_l[1] )
        self.mainLoop.player.setPosY( command_l[2] )
        self.mainLoop.player.setPosZ( command_l[3] )

    def pl_get_pos(self, _:list):
        """
        "pl_get_pos"
        
        플레이어의 현재 위치의 좌표를 인게임 콘솔에 출력합니다.
        """
        self.mainLoop.console.appendLogs("Player position: {:f}, {:f}, {:f}".format(*self.mainLoop.player.getPosXYZ()))

    def pl_set_degree(self, command_l:list):
        """
        "pl_set_degree (x degree: float) (y degree: float) (z degree: float)
        
        플레이어가 보는 방향을 설정합니다.
        인자는 degree 형식으로, 즉 360도 표현 방식으로 넣습니다.
        x, y, z는 회전축을 의미합니다.
        
        "pl_set_degree 0.0 180.0 0.0" -> 남쪽을 바라봅니다.
        """
        xAngle, yAngle, zAngle = self.mainLoop.player.getAngleXYZ()

        try:
            xAngle.setDegree(command_l[1])
            yAngle.setDegree(command_l[2])
            zAngle.setDegree(command_l[3])
        except:
            traceback.print_exc()

    def pl_get_degree(self, _:list):
        """
        "pl_get_degree"
        
        플레이어가 보는 방향을 degree 형식으로 인게임 콘솔에 출력합니다.
        """
        xAngle, yAngle, zAngle = self.mainLoop.player.getAngleXYZ()
        self.mainLoop.console.appendLogs("Player looking degree: {}, {}, {}".format(
            xAngle.getDegree(), yAngle.getDegree(), zAngle.getDegree()
        ))

    def pl_toggle_flashlight(self, command_l: list):
        """
        "pl_toggle_flashlight (0 or 1: int)"
        
        손전등을 켜고 끕니다.
        F키를 쓰는 게 훨씬 편합니다.
        
        예) "pl_toggle_flashlight 0" -> 손전등을 끕니다.
        """
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
            sys.exit(-1)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
