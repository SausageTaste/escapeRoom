from queue import Empty
from multiprocessing import Process, Queue

import obj_parse as op
import blueprints as bp


class ObjectLoader(Process):
    def __init__(self, toMainQueue:Queue, toProcQueue:Queue):
        super().__init__()

        self.toMainQueue = toMainQueue
        self.toProcQueue = toProcQueue

        self.run_b = True

    def run(self):
        while self.run_b:
            try:
                objName_s, objFileDir_s, mtlFileDir_s = self.toProcQueue.get_nowait()
            except Empty:
                pass
            else:
                self.__jobForOneObj( objName_s, objFileDir_s, mtlFileDir_s )

    def terminate(self):
        self.run_b = False
        try:
            super().terminate()
        except AttributeError:
            pass

        print("Thread 'ObjectLoader' terminated")

    def __jobForOneObj(self, objName_s, objFileDir_s, mtlFileDir_s) -> None:
        objBprint = self.__assembleObject(objName_s, objFileDir_s, mtlFileDir_s)
        self.toMainQueue.put(objBprint)

    @classmethod
    def __assembleObject(cls, objName_s, objFileDir_s, mtlFileDir_s) -> bp.ObjectDefineBlueprint:
        objBprint = bp.ObjectDefineBlueprint()
        objBprint.name_s = objName_s
        objBprint.static_b = False
        objBprint.initPos_t = (0.0, 0.0, 0.0)

        parsedObj_d = op.parseObj(objFileDir_s)
        parsedMtl_d = op.parseMtl(mtlFileDir_s)

        for renderer_s in parsedObj_d.keys():
            oneRenderer = parsedObj_d[renderer_s]
            oneMaterial = parsedMtl_d[ oneRenderer.mtl_s ]
            objBprint.rendererBlueprints_l.append( cls.__assembleRendererl(oneRenderer, oneMaterial) )

        if not cls.checkObjectDefine(objBprint):
            raise ValueError

        return objBprint

    @classmethod
    def __assembleRendererl(cls, oneRenderer:op.OneRenderer, oneMaterial:op.OneMaterial):
        renBprint = bp.RendererBlueprint()

        renBprint.name_s = oneRenderer.name_s
        renBprint.textureDir_s = oneMaterial.map_Kd_s
        renBprint.initPos_t = (0.0, 0.0, 0.0)
        renBprint.textureVerNum_f = 1.0
        renBprint.textureHorNum_f = 1.0
        renBprint.shininess_f = 32
        renBprint.specularStrength_f = 0.5

        renBprint.vertexNdarray = oneRenderer.vertexNdarray
        renBprint.texCoordNdarray = oneRenderer.textureCoordNdarray
        renBprint.normalNdarray = oneRenderer.normalNdarray

        cls.checkRendererAab(renBprint)

        return renBprint

    @staticmethod
    def checkObjectDefine(obp:bp.ObjectDefineBlueprint) -> bool:
        if obp.name_s is None:
            return False
        elif obp.static_b is None:
            return False
        elif obp.initPos_t is None:
            return False

        else:
            return True

    @staticmethod
    def checkRendererAab(renBprint: bp.RendererBlueprint) -> None:
        if renBprint.name_s is None:
            raise ValueError
        elif renBprint.textureDir_s is None:
            raise ValueError
        elif renBprint.initPos_t is None:
            raise ValueError
        elif renBprint.textureVerNum_f is None:
            raise ValueError
        elif renBprint.textureHorNum_f is None:
            raise ValueError
        elif renBprint.shininess_f is None:
            raise ValueError
        elif renBprint.specularStrength_f is None:
            raise ValueError

        elif renBprint.vertexNdarray is None:
            raise ValueError
        elif renBprint.texCoordNdarray is None:
            raise ValueError
        elif renBprint.normalNdarray is None:
            raise ValueError
