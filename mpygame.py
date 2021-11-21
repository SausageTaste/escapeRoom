from time import time, sleep
from typing import Tuple

import pygame as p


class FrameManager:
    def __init__(self, flagPrintFPS:bool=False, fpsUpdateCallback=None, fpsLimit_i:int=0):
        self.__clock = p.time.Clock()

        self.__flagPrintFPS = bool(flagPrintFPS)
        self.__fpsUpdateCallback = fpsUpdateCallback
        self.__fpsLimit_i = int(fpsLimit_i)

        self.__frameCount_i = 0
        self.__lastCountedTime_f = 0.0
        self.__frameDelta_f = 0.0
        self.__lastCountFPS_f = time()
        self.__fpsCounter_i = 0
        self.__lastFPS_i = 0
        self.__isFreshFps = False

    #### getters ####

    def getFrameCount(self) -> int:
        return self.__frameCount_i

    def getFrameDelta(self) -> float:
        if self.__frameDelta_f > 100.0:
            return 0.0
        else:
            return self.__frameDelta_f

    def getFPS(self) -> Tuple[int, bool]:
        if self.__isFreshFps:
            self.__isFreshFps = False
            return self.__lastFPS_i, True
        else:
            return self.__lastFPS_i, False

    #### setter ####

    def setPrintFPS(self, opt:bool) -> None:
        self.__flagPrintFPS = bool(opt)

    ####  ####

    def update(self) -> None:
        if self.__fpsLimit_i:
            self.__clock.tick(self.__fpsLimit_i)
        self.__frameDelta_f = time() - self.__lastCountedTime_f
        self.__lastCountedTime_f = time()

        self.__frameCount_i += 1
        if self.__frameCount_i > 10000:
            self.__frameCount_i = 0

        self.__fpsCounter_i += 1
        if time() - self.__lastCountFPS_f > 1.0:
            self.__lastFPS_i = self.__fpsCounter_i
            self.__fpsCounter_i = 0
            self.__lastCountFPS_f = time()
            self.__isFreshFps = True
            if self.__flagPrintFPS:
                print("FPS:", self.__lastFPS_i)
            if self.__fpsUpdateCallback is not None:
                self.__fpsUpdateCallback(self.__lastFPS_i)
