import os
from multiprocessing import Queue
from typing import List, Tuple, Optional
from queue import Empty

import OpenGL.GL as gl

import data_struct as ds
from buffer_manager import BufferManager
from texture_manager import TextureManager
from blueprints import ObjectDefineBlueprint, RendererBlueprint, ObjectObjStaticBlueprint
from object_loader import ObjectLoader
import const


class ObjectManager:
    def __init__(self):
        self.console = None

        self.__objTemplatesWatingVertices_l = []
        self.__objTemplatesWatingTextrue_l = []

        self.__objectTemplates_d = {}

        self.bufferManager = BufferManager()
        self.texMan = TextureManager()

        self.__toHereQueue = Queue()
        self.__toProcessQueue = Queue()
        self.objectLoader = ObjectLoader(self.__toHereQueue, self.__toProcessQueue)
        self.__haveThingsToGetFromProcess_i = 0

    def update(self) -> None:
        self.__fillObjectTemplateWithTexture()

        if self.__haveThingsToGetFromProcess_i:
            self.__popObjectBlueprintFromProcess()

    def terminate(self):
        try:
            self.objectLoader.terminate()
        except AttributeError:
            pass

        try:
            self.texMan.terminate()
        except AssertionError:
            pass

    def runProcesses(self):
        self.objectLoader.start()

    def requestObject(self, objInitInfo:"ObjectInitInfo") -> Optional[ds.Object]:
        self.update()

        if objInitInfo.objTemplateName_s in self.__objectTemplates_d.keys():
            if self.__objectTemplates_d[objInitInfo.objTemplateName_s] is None:
                return None
            else:
                objTemplate = self.__objectTemplates_d[objInitInfo.objTemplateName_s]
                obj = objTemplate.makeObject(
                    objInitInfo.name_s, objInitInfo.level, objInitInfo.initPos_t, objInitInfo.static_b,
                    objInitInfo.colliders_l, objInitInfo.colGroupTargets_l
                )
                self.console.appendLogs("Instancing object: {} ({})".format(objTemplate.templateName_s, objTemplate.refCount_i))
                return obj
        else:
            print("Object never created:", objInitInfo.objTemplateName_s)
            raise FileNotFoundError

    def dumpObjects(self, objTempNames_l:list) -> None:
        for objTempName_s in objTempNames_l:
            objTemplate = self.__objectTemplates_d[objTempName_s]
            objTemplate.refCount_i -= 1
            tempName_s = objTemplate.templateName_s

            self.console.appendLogs("Deleted an object instance: '{}' ({})".format(objTemplate.templateName_s, objTemplate.refCount_i))

            if objTemplate.refCount_i <= 0:
                trashes_l = objTemplate.terminate()
                for trash_t in trashes_l:
                    self.bufferManager.dumpVertexArray(trash_t[0])
                    self.bufferManager.dumpBuffer(trash_t[1])
                    self.bufferManager.dumpBuffer(trash_t[2])
                    self.bufferManager.dumpBuffer(trash_t[3])
                    self.texMan.dump(trash_t[4])

                del self.__objectTemplates_d[objTempName_s], objTemplate
                self.console.appendLogs( "Deleted ObjectTemplate: '{}'".format(tempName_s) )

    def giveObjectDefineBlueprint(self, objBprint:ObjectDefineBlueprint) -> None:
        if objBprint.name_s in self.__objectTemplates_d.keys():
            if self.__objectTemplates_d[objBprint.name_s] is not None:
                raise FileExistsError(objBprint.name_s)
        else:
            self.__objectTemplates_d[objBprint.name_s] = None

        objTemp = ObjectTemplate(
            objBprint.name_s, [self.__makeRendererFromBprint(xx) for xx in objBprint.rendererBlueprints_l],
            objBprint.colliders_l, objBprint.boundingBox
        )
        self.console.appendLogs("Created an object template: '{}'".format(objTemp.templateName_s))

        self.__objTemplatesWatingTextrue_l.append(objTemp)

    def giveObjectObjStaticBlueprint(self, objBprint:ObjectObjStaticBlueprint) -> None:
        if objBprint.objFileName_s in self.__objectTemplates_d.keys():
            return

        self.__objectTemplates_d[objBprint.objFileName_s] = None
        a = self.__findObjMtlDir(objBprint.objFileName_s)
        if a is None:
            self.console.appendLogs( "Failed to obj file: '{}'".format(objBprint.objFileName_s) )
        else:
            self.__toProcessQueue.put( (objBprint.objFileName_s, *a) )
            self.__haveThingsToGetFromProcess_i += 1

    def __fillObjectTemplateWithTexture(self):
        for x in range(len(self.__objTemplatesWatingTextrue_l) - 1, -1, -1):
            failedCount_i = 0

            objTemplate = self.__objTemplatesWatingTextrue_l[x]  # ObjectTemplate
            for y in range(len(objTemplate.renderers_l) - 1, -1, -1):
                aRenderer = objTemplate.renderers_l[y]
                if aRenderer.diffuseMap_i is None:
                    result = self.texMan.request(aRenderer.diffuseMapName_s)
                    if result is None:
                        failedCount_i += 1
                        continue
                    else:
                        aRenderer.diffuseMap_i = result
                        continue
                else:
                    pass

            if failedCount_i <= 0:
                self.__objectTemplates_d[objTemplate.templateName_s] = objTemplate
                del self.__objTemplatesWatingTextrue_l[x]

    def __popObjectBlueprintFromProcess(self):
        try:
            objBprint = self.__toHereQueue.get_nowait()
        except Empty:
            return None
        else:
            self.giveObjectDefineBlueprint(objBprint)

    def __makeRendererFromBprint(self, renBprint:RendererBlueprint) -> ds.Renderer:
        newRenderer = ds.Renderer(renBprint.name_s, renBprint.initPos_t, renBprint.static_b)
        vramUsage_i = 0

        ######## VAO ########

        newRenderer.vao_i = self.bufferManager.requestVertexArray()
        gl.glBindVertexArray(newRenderer.vao_i)

        ######## Vertex buffer ########

        size = renBprint.vertexNdarray.size * renBprint.vertexNdarray.itemsize
        newRenderer.vertexSize_i = renBprint.vertexNdarray.size // 3
        vramUsage_i += size

        newRenderer.vertexArrayBuffer_i = self.bufferManager.requestBuffer()
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, newRenderer.vertexArrayBuffer_i)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, size, renBprint.vertexNdarray, gl.GL_STATIC_DRAW)

        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glEnableVertexAttribArray(0)

        ######## Texture coord buffer ########

        size = renBprint.texCoordNdarray.size * renBprint.texCoordNdarray.itemsize
        vramUsage_i += size

        newRenderer.textureArrayBuffer_i = self.bufferManager.requestBuffer()
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, newRenderer.textureArrayBuffer_i)  # Bind the buffer.
        gl.glBufferData(gl.GL_ARRAY_BUFFER, size, renBprint.texCoordNdarray, gl.GL_STATIC_DRAW)  # Allocate memory.

        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)  # Defines vertex attributes. What are those?
        gl.glEnableVertexAttribArray(1)

        ########  ########

        size = renBprint.normalNdarray.size * renBprint.normalNdarray.itemsize
        vramUsage_i += size

        newRenderer.normalArrayBuffe_i = self.bufferManager.requestBuffer()
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, newRenderer.normalArrayBuffe_i)  # Bind the buffer.
        gl.glBufferData(gl.GL_ARRAY_BUFFER, size, renBprint.normalNdarray, gl.GL_STATIC_DRAW)  # Allocate memory.

        gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)  # Defines vertex attributes. What are those?
        gl.glEnableVertexAttribArray(2)

        ########  ########

        newRenderer.diffuseMapName_s = renBprint.textureDir_s

        newRenderer.textureVerNum_f = renBprint.textureVerNum_f
        newRenderer.textureHorNum_f = renBprint.textureHorNum_f
        newRenderer.shininess_f = renBprint.shininess_f
        newRenderer.specularStrength_f = renBprint.specularStrength_f
        newRenderer.vramUsage_i = vramUsage_i

        return newRenderer

    @staticmethod
    def __findObjMtlDir(objFileName_s:str) -> Optional[ Tuple[str, str] ]:
        objFileDir_s = ""
        mtlFileDir_s = ""

        for folderDir_s, _, files_l in os.walk(const.MODEL_DIR_s):
            for file_s in files_l:
                if objFileDir_s and mtlFileDir_s:
                    break

                if file_s == objFileName_s + ".obj":
                    if objFileDir_s:
                        raise FileExistsError("There are multiple '{}' files.".format(objFileName_s))
                    else:
                        objFileDir_s = "{}\\{}".format(folderDir_s, file_s)
                        continue
                elif file_s == objFileName_s + ".mtl":
                    if mtlFileDir_s:
                        raise FileExistsError("There are multiple '{}' files.".format(mtlFileDir_s))
                    else:
                        mtlFileDir_s = "{}\\{}".format(folderDir_s, file_s)
                        continue

        if objFileDir_s and mtlFileDir_s:
            return objFileDir_s, mtlFileDir_s
        else:
            return None


class ObjectTemplate:
    def __init__(self, templateName_s, renderers_l, colliders_l, boundingBox):
        self.refCount_i = 0
        self.usedOnce_b = False

        self.templateName_s = templateName_s

        self.renderers_l = renderers_l
        self.colliders_l = colliders_l

        self.boundingBox = boundingBox

    def __del__(self):
        print( "Deleted ObjectTemplate: '{}'".format(self.templateName_s) )

    def makeObject(self, name_s, parent, initPos_t, static_b:bool, colliders_l, colGroupTargets_l) -> ds.Object:
        self.refCount_i += 1
        self.usedOnce_b = True
        anObject = ds.Object(name_s, parent, initPos_t, static_b)
        anObject.renderers_l = self.renderers_l
        anObject.colliders_l = self.colliders_l + colliders_l
        anObject.boundingBox = self.boundingBox
        anObject.objTempName_s = self.templateName_s
        anObject.colGroupTargets_l = colGroupTargets_l

        return anObject

    def terminate(self) -> List[ Tuple[int, int, int, int, int] ]:
        rendererTrashes_l = []
        for renderer in self.renderers_l:
            rendererTrashes_l.append( renderer.terminate() )
        return rendererTrashes_l


class ObjectInitInfo:
    def __init__(self, name_s, objTemplateName_s, level, static_b, initPos_t, colGroupTargets_l, colliders_l):
        self.name_s = name_s
        self.objTemplateName_s = objTemplateName_s
        self.level = level

        self.static_b = static_b
        self.initPos_t = initPos_t

        self.colliders_l = colliders_l
        self.colGroupTargets_l = colGroupTargets_l
