from typing import Tuple, List, Optional

import OpenGL.GL as gl

from actor import Actor, ActorGeneral
from uniloc import UniformLocs
from uniloc_shadow import UniformLocsShadow


class Level(Actor):
    def __init__(self, name_s:str, initPos:Tuple[float, float, float]):
        super().__init__( name_s, None, initPos, True )

        self.boundingBox = None
        self.colGroups_l = None

        self.objects_l = []

        self.objectBlueprints_l = []
        self.objectObjInitInfo_l = []

        self.pointLights_l = []

    def __del__(self):
        # print( "Deleted Level: '{}'".format(self.getName()) )
        pass

    def terminate(self) -> List[str]:
        print("terminate", self.getName())
        objTempNames_l = []
        for obj in self.objects_l:
            objTempNames_l.append( obj.objTempName_s )

        del self.objects_l
        del self.objectBlueprints_l
        del self.objectObjInitInfo_l
        del self.pointLights_l

        return objTempNames_l

    def renderAll(self, uniLoc:UniformLocs) -> None:
        self.makePointLightDataReady(uniLoc)
        for obj in self.objects_l:
            obj.renderAll(uniLoc)

    def renderShadow(self, uniLocShadow) -> None:
        for obj in self.objects_l:
            obj.renderShadow(uniLocShadow)

    def printBlueprint(self) -> None:
        print(self.getName())
        for x in self.objectBlueprints_l:
            print(x)
            for y in x.__dir__():
                if not y.startswith("__"):
                    print("\t{} : {}".format(y, x.__getattribute__(y)))
            print()
            for z in x.rendererBlueprints_l:
                print("\t{}".format(z))
                for w in z.__dir__():
                    if not w.startswith("__"):
                        print("\t\t{} : {}".format(w, z.__getattribute__(w)))
            print()
            for z in x.colliders_l:
                print("\t{}".format(z))
                for w in z.__dir__():
                    if not w.startswith("__"):
                        print("\t\t{} : {}".format(w, z.__getattribute__(w)))
            print()

        print("Point Lights")
        for x in self.pointLights_l:
            print("\t{}".format(x))

    def findObjectByName(self, objectName_s:str) -> Optional["Object"]:
        for anObject in self.objects_l:
            if anObject.getName() == objectName_s:
                return anObject
        else:
            return None

    def makePointLightDataReady(self, uniLoc:UniformLocs) -> None:
        pointLightCount_i = 0
        pointLightPos_t = ()
        pointLightColor_t = ()
        pointLightMaxDist_t = ()

        for pointLight in self.pointLights_l:
            pointLightCount_i += 1
            pointLightPos_t += pointLight.getWorldXYZ(self)
            pointLightColor_t += pointLight.color_t
            pointLightMaxDist_t += (pointLight.maxDistance_f,)

        gl.glUniform1i( uniLoc.pointLightCount, pointLightCount_i )
        gl.glUniform3fv( uniLoc.pointLightPos, pointLightCount_i, pointLightPos_t )
        gl.glUniform3fv( uniLoc.pointLightColor, pointLightCount_i, pointLightColor_t )
        gl.glUniform1fv( uniLoc.pointLightMaxDistance, pointLightCount_i, pointLightMaxDist_t )

    def deleteAnObject(self, objName_s:str):
        for x in range(len(self.objects_l) -1, -1, -1):
            anObject = self.objects_l[x]
            if anObject.getName() == objName_s:
                tempName_s = anObject.objTempName_s
                del self.objects_l[x]
                return tempName_s
        else:
            return None


class Object(Actor):
    def __init__(self, name_s, parent, initPos, static_b):
        super().__init__(name_s, parent, initPos, static_b)

        self.renderers_l = []
        self.colliders_l = []

        self.boundingBox = None
        self.colGroupTargets_l = None

        self.objTempName_s = None

        self.seleted_b = False

    def __repr__(self) -> str:
        return "< {}.Object object at 0x{:0>16X}, name: {}, renderers: {}, colliders: {} >".format(
            __name__, id(self), self.getName(), self.renderers_l, self.colliders_l
        )

    def __del__(self):
        print( "Deleted Object: '{}'".format(self.getName()) )

    def renderAll(self, uniLoc:UniformLocs) -> None:
        if self.seleted_b:
            gl.glUniform1i(uniLoc.selected_i, 1)
            print("selected")
        else:
            gl.glUniform1i(uniLoc.selected_i, 0)
        for renderer in self.renderers_l:
            renderer.render(self, uniLoc)

    def renderShadow(self, uniLocShadow) -> None:
        for renderer in self.renderers_l:
            renderer.renderShadow(self, uniLocShadow)


class Renderer(ActorGeneral):
    def __init__( self, name_s:str, initPos:Tuple[float, float, float]=(0, 0, 0), static_b:bool=False ):
        super().__init__( name_s, static_b, initPos )

        self.vao_i = None
        self.vertexSize_i = None

        self.vertexArrayBuffer_i = None
        self.textureArrayBuffer_i = None
        self.normalArrayBuffe_i = None

        self.diffuseMap_i = None
        self.diffuseMapName_s = None

        self.textureVerNum_f = None
        self.textureHorNum_f = None

        self.specularStrength_f = None
        self.shininess_f = None

        self.staticLights_l = []

        self.vramUsage_i = -1

    def __del__(self):
        print( "Deleted Renderer: '{}' (vram: {:.2f} KB)".format(self.getName(), self.vramUsage_i / 1024.0) )

    def __repr__(self) -> str:
        return "< {}.Object object at 0x{:0>16X}, name: {}, vertexSize_i: {}, diffuseMap_i: {} >".format(
            __name__, id(self), self.getName(), self.vertexSize_i, self.diffuseMap_i
        )

    def render(self, parent:Actor, uniLoc:UniformLocs) -> None:
        gl.glBindVertexArray(self.vao_i);

        gl.glActiveTexture(gl.GL_TEXTURE0);
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.diffuseMap_i);

        gl.glUniformMatrix4fv(uniLoc.modelMatrix, 1, gl.GL_FALSE, self.getModelMatrix(parent));

        gl.glUniform1f(uniLoc.textureVerNum_f, self.textureVerNum_f);
        gl.glUniform1f(uniLoc.textureHorNum_f, self.textureHorNum_f);

        gl.glUniform1f(uniLoc.shininess, self.shininess_f);
        gl.glUniform1f(uniLoc.specularStrength, self.specularStrength_f);

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, self.vertexSize_i);

    def renderShadow(self, parent:Actor, uniLocShadow:UniformLocsShadow) -> None:
        gl.glBindVertexArray(self.vao_i);

        gl.glUniformMatrix4fv(uniLocShadow.modelMat, 1, gl.GL_FALSE, self.getModelMatrix(parent));

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, self.vertexSize_i);

    def terminate(self) -> Tuple[int, int, int, int, int]:
        del self.staticLights_l

        return self.vao_i, self.vertexArrayBuffer_i, self.textureArrayBuffer_i, self.normalArrayBuffe_i, self.diffuseMap_i
