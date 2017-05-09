from typing import Tuple, Optional
from time import time

import numpy as np

import mmath as mm


class RecursiveHierarchy(Exception):
    def __init__(self, name_s:str):
        self.name_s = str(name_s)

    def __str__(self):
        return "'{}' actor is its parent and child at the same time. WTF?".format(self.name_s)


class InvalidForStaticActor(Exception):
    def __init__(self, name_s:str):
        self.name_s = str(name_s)

    def __str__(self):
        return "'{}' is static actor so this method cannot be applied.".format(self.name_s)


class Actor:
    """
    This is parent class for all actors.
    Actor means objects that can move, rotate, resize.

    Instance who inherited this class is able to store its location, looking angles, size data.
    And using those data, it can make translate, rotate, scale matrix.
    Also it has some methods like one that makes it move according to its looking angle by using trigonometrical function/

    이것은 모든 Actor들의 부모 클래스입니다.
    Actor란, 움직이고 회전하고 크기를 조절할 수 있는 물체를 말합니다.

    이 클래스를 상속받은 인스턴스는 위치, 바라보는 각도, 크기 데이터를 저장할 수 있습니다.
    그리고 이 데이터를 이용하여 translate, rotate, scale 행렬을 만들 수 있습니다.
    또한 삼각함수를 이용해여 보는 방향에 따라 이동을 하는 메소드 등 여러 메소드를 가집니다.
    """
    def __init__(self, name_s:str, parent:"Actor"=None, initPos:Tuple[float, float, float]=(0.0, 0.0, 0.0), static_b:bool=False):
        self.__static_b = False

        self.__name_s = str(name_s)

        self.__parent = None
        self.setParent(parent)

        self.__pos_l = [ float(initPos[0]), float(initPos[1]), float(initPos[2]) ]
        self.__angles_l = [mm.Angle(0, static_b), mm.Angle(0, static_b), mm.Angle(0, static_b)]
        self.__scales_l = [1.0, 1.0, 1.0]

        self.__static_b = bool(static_b)

        self.__lastUpdateTime_f = time()

    ######## Getters for private attributes ########

    def getParent(self) -> "Actor":
        return self.__parent

    def getPosX(self) -> float:
        return self.__pos_l[0]

    def getPosY(self) -> float:
        return self.__pos_l[1]

    def getPosZ(self) -> float:
        return self.__pos_l[2]

    def getAngleX(self) -> mm.Angle:
        return self.__angles_l[0]

    def getAngleY(self) -> mm.Angle:
        return self.__angles_l[1]

    def getAngleZ(self) -> mm.Angle:
        return self.__angles_l[2]

    def getScaleX(self) -> float:
        return self.__scales_l[0]

    def getScaleY(self) -> float:
        return self.__scales_l[1]

    def getScaleZ(self) -> float:
        return self.__scales_l[2]

    def getStatic(self) -> bool:
        return self.__static_b

    def getName(self) -> str:
        return self.__name_s

    def getTimeDelta(self) -> float:
        thisTime_f = time()
        timeDelta_f = thisTime_f - self.__lastUpdateTime_f
        self.__lastUpdateTime_f = thisTime_f
        return timeDelta_f

    ######## Setters for private attributes ########

    def setParent(self, parent:"Actor") -> None:
        if parent is None:
            self.__parent = None
        elif not isinstance(parent, Actor):
            raise ValueError( "Invalid type for being a parent: {}".format(type(parent)) )
        else:
            if self.getStatic() and not parent.getStatic():
                raise InvalidForStaticActor(self.getName())
            else:
                self.__parent = parent
                if self.getHierarchicalDepth() == -1:
                    raise RecursiveHierarchy

    def setPosX(self, x:float) -> None:
        if self.getStatic():
            raise InvalidForStaticActor(self.getName())
        self.__pos_l[0] = float(x)

    def setPosY(self, y:float) -> None:
        if self.getStatic():
            raise InvalidForStaticActor(self.getName())
        self.__pos_l[1] = float(y)

    def setPosZ(self, z:float) -> None:
        if self.getStatic():
            raise InvalidForStaticActor(self.getName())
        self.__pos_l[2] = float(z)

    def setScaleXYZ(self, x, y, z):
        self.__scales_l[0] = float(x)
        self.__scales_l[1] = float(y)
        self.__scales_l[2] = float(z)

    ######## Getters for private arribs without accessing tham ########

    def getPosXYZ(self) -> Tuple[float, float, float]:
        return self.getPosX(), self.getPosY(), self.getPosZ()

    def getAngleXYZ(self) -> Tuple[mm.Angle, mm.Angle, mm.Angle]:
        return self.getAngleX(), self.getAngleY(), self.getAngleZ()

    def getScaleXYZ(self) -> Tuple[float, float, float]:
        return self.getScaleX(), self.getScaleY(), self.getScaleZ()

    def getWorldXYZ(self) -> Tuple[float, float, float]:
        xWorld_f, yWorld_f, zWorld_f = self.getPosXYZ()

        parent = self.getParent()
        if parent is not None:
            xParent_f, yParent_f, zParent_f = parent.getWorldXYZ()
            xWorld_f += xParent_f
            yWorld_f += yParent_f
            zWorld_f += zParent_f

        return xWorld_f, yWorld_f, zWorld_f

    def getWorldAngleXYZ(self) -> Tuple[mm.Angle, mm.Angle, mm.Angle]:
        xAngle = self.getAngleX()
        yAngle = self.getAngleY()
        zAngle = self.getAngleZ()

        parent = self.getParent()
        if parent is not None:
            xParent, yParent, zParent = parent.getWorldAngleXYZ()
            xAngle += xParent
            yAngle += yParent
            zAngle += zParent

        return xAngle, yAngle, zAngle

    def getWorldDegreeXYZ(self) -> Tuple[float, float, float]:
        xAngle, yAngle, zAngle = self.getWorldAngleXYZ()
        return xAngle.getDegree(), yAngle.getDegree(), zAngle.getDegree()

    def getModelMatrix(self) -> np.ndarray:
        a = mm.getScaleMat4(*self.getScaleXYZ()).dot(
            mm.getRotateXYZMat4(1, self.getAngleX().getDegree(), self.getAngleY().getDegree(), self.getAngleZ().getDegree())
        ).dot(
            mm.getTranslateMat4(*self.getPosXYZ())
        )

        if self.getParent() is not None:
            a = a.dot(self.getParent().getModelMatrix())

        return a

    ######## Setters for private arribs without accessing tham ########

    def setDegrees(self, xDegree_f:float, yDegree_f:float, zDegree_f:float) -> None:
        self.getAngleX().setDegree(xDegree_f)
        self.getAngleY().setDegree(yDegree_f)
        self.getAngleZ().setDegree(zDegree_f)

    ######## Tools to move ########

    def moveAround(self, directionVec4, distance_f:float) -> None:
        #directionVec4 = directionVec4.transform( mm.getRotateXYZMat4(1, 0, -self.getAngleY().getDegree(), 0) )
        directionVec4 = directionVec4.transform( mm.getRotateYMat4(-self.getAngleY().getDegree()) )
        self.setPosX(self.getPosX() + directionVec4.getX()*distance_f)
        self.setPosZ(self.getPosZ() + directionVec4.getZ()*distance_f)

    ########  ########

    def validateValuesForCamera(self) -> None:
        xAngle = self.getAngleX()
        if 90.0 < xAngle.getDegree() <= 180:
            xAngle.setDegree(90.0)
        elif 180.0 < xAngle.getDegree() <= 270:
            xAngle.setDegree(270.0)

    def getHierarchicalDepth(self) -> int:
        try:
            return self.__getHierarchicalDepth()
        except RecursionError:
            return -1

    def __getHierarchicalDepth(self) -> int:
        c = 1
        parent = self.getParent()
        if parent is not None:
            c += parent.__getHierarchicalDepth()
        return c


class ActorGeneral:
    def __init__(self, name_s:str, static_b:bool=False, initPos_t:Tuple[float, float, float]=(0.0, 0.0, 0.0)):
        self.__static_b = False

        self.__name_s = str(name_s)

        self.__pos_l = [ float(initPos_t[0]), float(initPos_t[1]), float(initPos_t[2]) ]
        self.__angles_l = [mm.Angle(0, static_b), mm.Angle(0, static_b), mm.Angle(0, static_b)]
        self.__scales_l = [1.0, 1.0, 1.0]

        self.__static_b = bool(static_b)

    ######## Getters for private attributes ########

    def getPosX(self) -> float:
        return self.__pos_l[0]

    def getPosY(self) -> float:
        return self.__pos_l[1]

    def getPosZ(self) -> float:
        return self.__pos_l[2]

    def getAngleX(self) -> mm.Angle:
        return self.__angles_l[0]

    def getAngleY(self) -> mm.Angle:
        return self.__angles_l[1]

    def getAngleZ(self) -> mm.Angle:
        return self.__angles_l[2]

    def getScaleX(self) -> float:
        return self.__scales_l[0]

    def getScaleY(self) -> float:
        return self.__scales_l[1]

    def getScaleZ(self) -> float:
        return self.__scales_l[2]

    def getStatic(self) -> bool:
        return self.__static_b

    def getName(self) -> str:
        return self.__name_s

    ######## Setters for private attributes ########

    def setPosX(self, x:float) -> None:
        if self.getStatic():
            raise InvalidForStaticActor(self.getName())
        self.__pos_l[0] = float(x)

    def setPosY(self, y:float) -> None:
        if self.getStatic():
            raise InvalidForStaticActor(self.getName())
        self.__pos_l[1] = float(y)

    def setPosZ(self, z:float) -> None:
        if self.getStatic():
            raise InvalidForStaticActor(self.getName())
        self.__pos_l[2] = float(z)

    ######## Getters for private arribs without accessing tham ########

    def getPosXYZ(self) -> Tuple[float, float, float]:
        return self.getPosX(), self.getPosY(), self.getPosZ()

    def getAngleXYZ(self) -> Tuple[mm.Angle, mm.Angle, mm.Angle]:
        return self.getAngleZ(), self.getAngleY(), self.getAngleZ()

    def getScaleXYZ(self) -> Tuple[float, float, float]:
        return self.getScaleX(), self.getScaleY(), self.getScaleZ()

    def getWorldXYZ(self, parent:Optional[Actor]=None) -> Tuple[float, float, float]:
        xWorld_f, yWorld_f, zWorld_f = self.getPosXYZ()

        if parent is not None:
            xParent_f, yParent_f, zParent_f = parent.getWorldXYZ()
            xWorld_f += xParent_f
            yWorld_f += yParent_f
            zWorld_f += zParent_f

        return xWorld_f, yWorld_f, zWorld_f

    def getWorldAngleXYZ(self, parent:Optional[Actor]=None) -> Tuple[mm.Angle, mm.Angle, mm.Angle]:
        xAngle = self.getAngleX()
        yAngle = self.getAngleY()
        zAngle = self.getAngleZ()

        if parent is not None:
            xParent, yParent, zParent = parent.getWorldAngleXYZ()
            xAngle += xParent
            yAngle += yParent
            zAngle += zParent

        return xAngle, yAngle, zAngle

    def getWorldDegreeXYZ(self, parent) -> Tuple[float, float, float]:
        xAngle, yAngle, zAngle = self.getWorldAngleXYZ(parent)
        return xAngle.getDegree(), yAngle.getDegree(), zAngle.getDegree()

    def getModelMatrix(self, parent:Optional[Actor]=None) -> np.ndarray:
        a = mm.getScaleMat4(*self.getScaleXYZ()).dot(
            mm.getRotateXYZMat4(1, self.getAngleX().getDegree(), self.getAngleY().getDegree(), self.getAngleZ().getDegree())
        ).dot(
            mm.getTranslateMat4(*self.getPosXYZ())
        )

        if parent is not None:
            a = a.dot(parent.getModelMatrix())

        return a

    ######## Setters for private arribs without accessing tham ########

    def setDegrees(self, xDegree_f:float, yDegree_f:float, zDegree_f:float) -> None:
        self.getAngleX().setDegree(xDegree_f)
        self.getAngleY().setDegree(yDegree_f)
        self.getAngleZ().setDegree(zDegree_f)

    ######## Tools to move ########

    def moveAround(self, directionVec4, distance_f:float) -> None:
        #directionVec4 = directionVec4.transform( mm.getRotateXYZMat4(1, 0, -self.getAngleY().getDegree(), 0) )
        directionVec4 = directionVec4.transform( mm.getRotateYMat4(-self.getAngleY().getDegree()) )
        self.setPosX(self.getPosX() + directionVec4.getX()*distance_f)
        self.setPosZ(self.getPosZ() + directionVec4.getZ()*distance_f)

    ########  ########

    def __checkParentValid(self, parent:"Actor") -> bool:
        if parent is None:
            return True
        else:
            if self.getStatic() and not parent.getStatic():
                raise InvalidForStaticActor(self.getName())
