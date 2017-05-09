import os
from typing import Optional, Tuple
from multiprocessing import Process, Queue
from queue import Empty
from time import time

from PIL import Image
import numpy as np
import OpenGL.GL as gl

import const


class TextureLoader(Process):
    def __init__(self, toMainQueue:Queue, toProcQueue:Queue):
        super().__init__()

        self.toMainQueue = toMainQueue
        self.toProcQueue = toProcQueue

        self.run_b = True

    def run(self):
        while True:
            try:
                textureName_s, fileDir_s = self.toProcQueue.get_nowait()
            except Empty:
                pass
            else:
                self.__job(textureName_s, fileDir_s)

    def terminate(self):
        self.run_b = False
        try:
            super().terminate()
        except AttributeError:
            pass

        print("Thread 'TextureLoader' terminated")

    def __job(self, textureName_s, fileDir_s):
        imgData = self.__loadImg(fileDir_s)
        imgData.name_s = textureName_s
        imgData.success_b = True
        imgData.checkIntegrity()

        self.toMainQueue.put(imgData)

    @staticmethod
    def __loadImg(fileDir_s) -> "LoadedImageData":
        imgData = LoadedImageData()

        aImg = Image.open(fileDir_s)
        imgData.width_i = aImg.size[0]
        imgData.height_i = aImg.size[1]
        try:
            image_bytes = aImg.tobytes("raw", "RGBA", 0, -1)
            imgData.alpha_b = True
        except ValueError:
            image_bytes = aImg.tobytes("raw", "RGBX", 0, -1)
            imgData.alpha_b = False
        imgData.ndarray = np.array([x/255 for x in image_bytes], dtype=np.float32)

        return imgData


class TextureManager:
    def __init__(self):
        self.__textures_d = {}

        self.__toMainQueue = Queue()
        self.__toProcQueue = Queue()
        self.__texLoader = TextureLoader(self.__toMainQueue, self.__toProcQueue)
        self.__waitingForImgData_i = 0
        self.__texLoader.start()

    def terminate(self):
        self.__texLoader.terminate()

    def request(self, textureName_s:str) -> Optional[int]:
        self.__popTexNdarrayFromProc()

        if textureName_s in self.__textures_d:
            aTexture = self.__textures_d[textureName_s]
            if aTexture is None:
                return None
            else:
                aTexture.refCount_i += 1
                aTexture.usedOnce_b = True
                print("Instancing texture: '{}' ({})".format( textureName_s, aTexture.refCount_i ))
                return aTexture.texId_i
        else:
            self.__textures_d[textureName_s] = None
            self.__load(textureName_s)
            return None

    def dump(self, texId_i:int) -> None:
        deleteQueue_l = []
        for textureName_s in self.__textures_d:
            texture = self.__textures_d[textureName_s]
            if texture.texId_i == texId_i:
                texture.refCount_i -= 1
                print("Deleted an instance of texture: '{}' ({})".format(textureName_s, texture.refCount_i))
                if texture.refCount_i < 1:
                    gl.glDeleteTextures( texture.texId_i )
                    print("Deleted texture: '{}' (vram: {:.2f} KB)".format(textureName_s, texture.texSize_f))
                    deleteQueue_l.append( textureName_s )

        for textureName_s in deleteQueue_l:
            del self.__textures_d[textureName_s]

    def __load(self, textureName_s:str) -> None:
        fileDir_s = self.__findTexFile(textureName_s)
        self.__toProcQueue.put( (textureName_s, fileDir_s) )
        self.__waitingForImgData_i += 1

        #
        #texId_i, texSize_f = self.__getTextureId(fileDir_s)
        #self.__textures_d[textureName_s] = Texture( texId_i, texSize_f )

    def __popTexNdarrayFromProc(self):
        if self.__waitingForImgData_i <= 0:
            return
        st = time()
        try:
            imgData = self.__toMainQueue.get_nowait()
        except Empty:
            pass
        else:
            if not imgData.success_b:
                raise FileNotFoundError("Failed to load texture in Process")

            texId_i, texSize_f = self.__makeTextureIdFromNdarray(imgData)
            self.__textures_d[imgData.name_s] = Texture(texId_i, texSize_f)
            self.__waitingForImgData_i -= 1
            print("Textrue loaded: '{}' ({})".format(imgData.name_s, time() - st))

    @staticmethod
    def __findTexFile(textureName_s:str) -> str:
        for x_s in os.listdir(const.TEXTURE_DIR_s):
            if x_s == textureName_s:
                return const.TEXTURE_DIR_s + x_s
        else:
            raise FileNotFoundError(textureName_s)

    @staticmethod
    def __makeTextureIdFromNdarray(imgData:"LoadedImageData") -> Tuple[int, float]:
        texId = int( gl.glGenTextures(1) )
        if texId is None:
            raise FileNotFoundError("Failed to get texture id.")

        gl.glBindTexture(gl.GL_TEXTURE_2D, texId)
        gl.glTexStorage2D(gl.GL_TEXTURE_2D, 6, gl.GL_RGBA32F, imgData.width_i, imgData.height_i)

        gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, imgData.width_i, imgData.height_i, gl.GL_RGBA, gl.GL_FLOAT, imgData.ndarray)

        texSize_f = imgData.width_i*imgData.height_i*4*4/1024

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BASE_LEVEL, 0)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAX_LEVEL, 6)

        # Alpha
        #gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        #gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

        if 1:
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        else:
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST_MIPMAP_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        return int(texId), float(texSize_f + texSize_f/3.0)

class Texture:
    def __init__(self, texId_i:int, texSize_f:float):
        self.texId_i = texId_i
        self.texSize_f = float(texSize_f)
        self.refCount_i = 0
        self.usedOnce_b = False


class LoadedImageData:
    def __init__(self):
        self.success_b = None

        self.name_s = None
        self.ndarray = None
        self.width_i = None
        self.height_i = None

        self.alpha_b = None

    def checkIntegrity(self):
        if self.success_b is None:
            raise ValueError
        elif self.name_s is None:
            raise ValueError
        elif self.ndarray is None:
            raise ValueError
        elif self.width_i is None:
            raise ValueError
        elif self.height_i is None:
            raise ValueError
        elif self.alpha_b is None:
            raise ValueError
