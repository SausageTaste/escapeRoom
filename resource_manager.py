import os
from time import time
from typing import Optional, Generator
from multiprocessing import Queue
from queue import Empty

import OpenGL.GL as gl

from level_loader import LevelLoader
from data_struct import Level, Object
from object_manager import ObjectManager, ObjectInitInfo
import blueprints as bp
from uniloc import UniformLocs
from overlay_ui import OverlayUiManager
from curstate import GlobalStates


class ResourceManager:
    def __init__(self, globalStates:GlobalStates):
        self.globalStates = globalStates

        self._levelsWaitingObj_l = []
        self._levels_l = []

        self._watingForLevel_i = 0
        self._fromLevelLoaderQueue = Queue()
        self._toLevelLoaderQueue = Queue()

        self._levelLoader = LevelLoader(self._fromLevelLoaderQueue, self._toLevelLoaderQueue)

        self._objectMan = ObjectManager()

        self.overlayUiMan = OverlayUiManager(self._objectMan.texMan, self.globalStates)
        self.console = self.overlayUiMan.consoleWin

        self._objectMan.console = self.console

    def renderAll(self, uniLoc:UniformLocs) -> None:
        for level in self._levels_l:
            level.renderAll(uniLoc)

        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDisable(gl.GL_DEPTH_TEST)

        self.overlayUiMan.render()

    def resize(self):
        self.overlayUiMan.resize()

    def renderShadow(self, uniLocShadow) -> None:
        for level in self._levels_l:
            level.renderShadow(uniLocShadow)

    def levelsGen(self) -> Generator[Level, None, None]:
        for level in self._levels_l:
            yield level

    def terminate(self) -> None:
        self._objectMan.terminate()

        for level in self._levels_l:
            objTempNames_l = level.terminate()
            self._objectMan.dumpObjects(objTempNames_l)

        del self._levels_l, self._levelsWaitingObj_l

        try:
            self._levelLoader.terminate()
        except AttributeError:
            pass

    def runProcesses(self) -> None:
        self._levelLoader.start()
        self._objectMan.runProcesses()

    def update(self) -> None:
        self.__popFromLevelLoader()

        self.__fillLevelWithObjects()

    def findLevelByName(self, levelName_s:str) -> Optional[Level]:
        for level in self._levels_l:
            if level.getName() == levelName_s:
                return level
        else:
            return None

    def findObjectInLevelByName(self, levelName_s:str, objectName_s:str) -> Optional[Object]:
        level = self.findLevelByName(levelName_s)
        if level is None:
            return None
        else:
            return level.findObjectByName(objectName_s)

    def requestLevelLoad(self, levelName_s:str, waitTime_f:float=0.0) -> None:
        for level in self._levels_l:
            if level.getName() == levelName_s:
                print("Already loaded level:", levelName_s)
                self.console.appendLogs( "Already loaded level: '{}'".format(levelName_s) )
                break
        else:
            smllFileDir_s = self.__findLevelDir(levelName_s + ".smll")
            self._toLevelLoaderQueue.put(smllFileDir_s)
            self._watingForLevel_i += 1

        if waitTime_f <= 0.0:
            return

        waitStartTime_f = time()
        while time() - waitStartTime_f < waitTime_f:
            self.update()
            if self.getLevelWithNameInLevelsList(levelName_s) is None:
                continue
            else:
                if self.getLevelWithNameInLevelWaitingObjList(levelName_s) is None:
                    continue
                else:
                    return
        else:
            raise FileNotFoundError("Level loading time out")

    def deleteLevel(self, levelName_s:str) -> None:
        for x, level in enumerate(self._levels_l):
            if level.getName() == levelName_s:
                del self._levels_l[x]
                self._objectMan.dumpObjects( level.terminate() )

        for x, level in enumerate(self._levelsWaitingObj_l):
            if level.getName() == levelName_s:
                del self._levels_l[x]

    def deleteAllLevels(self):
        for x in range(len(self._levels_l) - 1, -1, -1):
            level = self._levels_l[x]
            del self._levels_l[x]
            self._objectMan.dumpObjects( level.terminate() )

        for x in range(len(self._levelsWaitingObj_l) - 1, -1, -1):
            del self._levels_l[x]

    def deleteAnObject(self, levelName_s:str, objectName_s:str) -> bool:
        level = self.findLevelByName(levelName_s)
        if level is None:
            return False
        else:
            objTempName_s = level.deleteAnObject(objectName_s)
            if objTempName_s is not None:
                self._objectMan.dumpObjects( [objTempName_s] )
                self.console.appendLogs("An onject '{}' in level '{}' has been deleted.".format(objectName_s, levelName_s))
            else:
                return False

    def getLevelWithNameInLevelsList(self, levelName_s:str) -> Optional[Level]:
        for level in self._levels_l:
            if level.getName() == levelName_s:
                return level
        else:
            return None

    def getLevelWithNameInLevelWaitingObjList(self, levelName_s:str) -> Optional[Level]:
        for level in self._levelsWaitingObj_l:
            if level.getName() == levelName_s:
                return level
        else:
            return None

    @staticmethod
    def __findLevelDir(levelName_s:str) -> str:
        for x_s in os.listdir(".\\assets\\levels\\"):
            if levelName_s == x_s:
                return ".\\assets\\levels\\" + x_s
        else:
            raise FileNotFoundError(levelName_s)

    def __popFromLevelLoader(self) -> None:
        if self._watingForLevel_i:
            try:
                result = self._fromLevelLoaderQueue.get_nowait()
            except Empty:
                return
            else:
                self._watingForLevel_i -= 1
                if isinstance(result, tuple):  # Failed to load a level.
                    if result[0] == -1:  # File does not exist.
                        print( "(Error) File not found:", result[1] )
                elif isinstance(result, Level):
                    self._levelsWaitingObj_l.append(result)
                    self._levels_l.append(result)
                    text_s = "Level loaded: '{}'".format(result.getName())
                    print( text_s )
                    self.console.appendLogs( text_s )
                else:
                    raise ValueError( "Recived wrong data type from LevelLoader: {}".format(type(result)) )

    def __fillLevelWithObjects(self) -> None:
        for x in range(len(self._levelsWaitingObj_l) - 1, -1, -1):
            level = self._levelsWaitingObj_l[x]
            for y in range(len(level.objectBlueprints_l) - 1, -1, -1):
                objBprint = level.objectBlueprints_l[y]
                if isinstance(objBprint, bp.ObjectDefineBlueprint):
                    self._objectMan.giveObjectDefineBlueprint(objBprint)
                    level.objectObjInitInfo_l.append( ObjectInitInfo(
                        objBprint.name_s, objBprint.name_s, level, objBprint.static_b, objBprint.initPos_t,
                        objBprint.colGroupTargets_l, []
                    ) )
                    del level.objectBlueprints_l[y]
                elif isinstance(objBprint, bp.ObjectUseBlueprint):
                    level.objectObjInitInfo_l.append( ObjectInitInfo(
                        objBprint.name_s, objBprint.templateName_s, level, objBprint.static_b, objBprint.initPos_t,
                        objBprint.colGroupTargets_l, []
                    ) )
                    del level.objectBlueprints_l[y]
                elif isinstance(objBprint, bp.ObjectObjStaticBlueprint):
                    self._objectMan.giveObjectObjStaticBlueprint(objBprint)
                    level.objectObjInitInfo_l.append( ObjectInitInfo(
                        objBprint.name_s, objBprint.objFileName_s, level, objBprint.static_b, objBprint.initPos_t,
                        objBprint.colGroupTargets_l, objBprint.colliders_l
                    ) )
                    del level.objectBlueprints_l[y]
                else:
                    raise ValueError

            for y in range(len(level.objectObjInitInfo_l) - 1, -1, -1):
                objInitInfo = level.objectObjInitInfo_l[y]
                result = self._objectMan.requestObject( objInitInfo )
                if result is not None:
                    del level.objectObjInitInfo_l[y]
                    level.objects_l.append(result)

            if len( level.objectObjInitInfo_l ) <= 0:
                del self._levelsWaitingObj_l[x]
