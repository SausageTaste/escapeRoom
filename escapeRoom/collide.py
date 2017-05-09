from typing import Tuple, Optional, Union, List

import mmath as mm
from actor import Actor, ActorGeneral
import myclib as c


######## Interface ########

def checkCollision(fromCol:Union["Aabb"], fromColParent:Optional[Actor], toCol:Union["Aabb"], toColParant:Optional[Actor]) -> bool:
    if isinstance(fromCol, Aabb) and isinstance(toCol, Aabb):
        return checkAabbAabb(fromCol, fromColParent, toCol, toColParant)
    else:
        raise ValueError( "Not supported types: {}, {}".format( type(fromCol), type(toCol) ) )

def getDistaceToPushBack(fromCol:Union["Aabb"], fromColParent:Optional[Actor], toCol:Union["Aabb"], toColParant:Optional[Actor]) -> Tuple[float, float, float, float, float, float]:
    if isinstance(fromCol, Aabb) and isinstance(toCol, Aabb):
        return getDistanceToPushBackAabbAabb_C(fromCol, fromColParent, toCol, toColParant)
    else:
        raise ValueError( "Not supported types: {}, {}".format( type(fromCol), type(toCol) ) )

######## Check if colliding ########

def checkAabbAabb(a:"Aabb", parentA:Actor, b:"Aabb", parentB:Actor) -> bool:
    xMaxA, yMaxA, zMaxA = a.getWorldMaxXYZ(parentA)
    xMinA, yMinA, zMinA = a.getWorldMinXYZ(parentA)

    xMaxB, yMaxB, zMaxB = b.getWorldMaxXYZ(parentB)
    xMinB, yMinB, zMinB = b.getWorldMinXYZ(parentB)

    if xMaxA < xMinB:
        return False
    elif xMinA > xMaxB:
        return False
    elif yMaxA < yMinB:
        return False
    elif yMinA > yMaxB:
        return False
    elif zMaxA < zMinB:
        return False
    elif zMinA > zMaxB:
        return False
    else:
        return True

def checkAabbSegment(aabb:"Aabb", parentA:Optional[Actor],  seg:"Segment", parentB:Optional[Actor]):
    xSegPos_f, ySegPos_f, zSegPos_f = seg.getSegmentPos(parentB)
    xSegVec_f, ySegVec_f, zSegVec_f = seg.getSegmentDirection(parentB)

    xMax_f, yMax_f, zMax_f = aabb.getWorldMaxXYZ(parentA)
    xMin_f, yMin_f, zMin_f = aabb.getWorldMinXYZ(parentA)

    if xSegVec_f == 0.0:
        if (xSegPos_f < xMin_f) or (xSegPos_f > xMax_f):
            return False
        tx_min = 0.0
        tx_max = 1.0
    else:
        t0 = ( xMin_f - xSegPos_f ) / xSegVec_f
        t1 = ( xMax_f - xSegPos_f ) / xSegVec_f
        if t0 < t1:
            tx_min = t0
            tx_max = t1
        else:
            tx_min = t1
            tx_max = t0

        if (tx_max < 0.0) or (tx_min > 1.0):
            return False

    t_min = tx_min
    t_max = tx_max

    if ySegVec_f == 0.0:
        if (ySegPos_f < yMin_f) or (ySegPos_f > yMax_f):
            return False
        ty_min = 0.0
        ty_max = 1.0
    else:
        t0 = (yMin_f - ySegPos_f) / ySegVec_f
        t1 = (yMax_f - ySegPos_f) / ySegVec_f
        if t0 < t1:
            ty_min = t0
            ty_max = t1
        else:
            ty_min = t1
            ty_max = t0
        if (ty_max < 0.0) or (ty_min > 1.0):
            return False

    if (t_max < ty_min) or (t_min > ty_max):
        return False
    if t_min < ty_min:
        t_min = ty_min
    if t_max > ty_max:
        t_max = ty_max

    if zSegVec_f == 0.0:
        if (zSegPos_f < zMin_f) or (zSegPos_f > zMax_f):
            return False
        tz_min = 0.0
        tz_max = 1.0
    else:
        t0 = (zMin_f - zSegPos_f) / zSegVec_f
        t1 = (zMax_f - zSegPos_f) / zSegVec_f
        if t0 < t1:
            tz_min = t0
            tz_max = t1
        else:
            tz_min = t1
            tz_max = t0
        if (tz_max < 0.0) or (tz_min > 1.0):
            return False

    if (t_max < tz_min) or (t_min > tz_max):
        return False
    if t_min < tz_min:
        t_min = tz_min
    if t_max > tz_max:
        t_max = tz_max

    if (t_min > 1.0) or (t_max < 0.0):
        return False
    else:
        return True

######## Return how far shoud it move to resolve collision ########

def getDistanceToPushBackAabbAabb(a:"Aabb", parentA:Actor, b:"Aabb", parentB:Actor) -> Tuple[float, float, float, float, float, float]:
    xMaxA, yMaxA, zMaxA = a.getWorldMaxXYZ(parentA)
    xMinA, yMinA, zMinA = a.getWorldMinXYZ(parentA)

    xMaxB, yMaxB, zMaxB = b.getWorldMaxXYZ(parentB)
    xMinB, yMinB, zMinB = b.getWorldMinXYZ(parentB)

    xOne = xMaxA - xMinB
    xTwo = xMinA - xMaxB
    xDistance = xOne if abs(xOne) < abs(xTwo) else xTwo

    yOne = yMaxA - yMinB
    yTwo = yMinA - yMaxB
    yDistance = yOne if abs(yOne) < abs(yTwo) else yTwo

    zOne = zMaxA - zMinB
    zTwo = zMinA - zMaxB
    zDistance = zOne if abs(zOne) < abs(zTwo) else zTwo

    aWeight_f = a.getWeight()
    bWeight_f = b.getWeight()
    weightSum_f = aWeight_f + bWeight_f
    if weightSum_f == 0.0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    aMul_f = aWeight_f / weightSum_f
    bMul_f = bWeight_f / weightSum_f

    xForA_f = -xDistance*aMul_f
    yForA_f = -yDistance*aMul_f
    zForA_f = -zDistance*aMul_f

    xForB_f = xDistance*bMul_f
    yForB_f = yDistance*bMul_f
    zForB_f = zDistance*bMul_f

    if abs(xForA_f) <= abs(yForA_f) and abs(xForA_f) <= abs(zForA_f):
        return xForA_f, 0.0, 0.0, xForB_f, 0.0, 0.0
    elif abs(yForA_f) < abs(xForA_f) and abs(yForA_f) < abs(zForA_f):
        return 0.0, yForA_f, 0.0, 0.0, yForB_f, 0.0
    elif abs(zForA_f) < abs(xForA_f) and abs(zForA_f) < abs(yForA_f):
        return 0.0, 0.0, zForA_f, 0.0, 0.0, zForB_f
    else:
        raise ValueError(xForA_f, yForA_f, zForA_f)

def getDistanceToPushBackAabbAabb_C(a:"Aabb", parentA:Actor, b:"Aabb", parentB:Actor) -> Tuple[float, float, float, float, float, float]:
    xMaxA, yMaxA, zMaxA = a.getWorldMaxXYZ(parentA)
    xMinA, yMinA, zMinA = a.getWorldMinXYZ(parentA)

    xMaxB, yMaxB, zMaxB = b.getWorldMaxXYZ(parentB)
    xMinB, yMinB, zMinB = b.getWorldMinXYZ(parentB)

    aWeight_f = a.getWeight()
    bWeight_f = b.getWeight()

    return c.getDistanceToPushBackAabbAabb( (
        xMaxA, yMaxA, zMaxA, xMinA, yMinA, zMinA, xMaxB, yMaxB, zMaxB, xMinB, yMinB, zMinB, aWeight_f, bWeight_f
    ) )


class Aabb(ActorGeneral):
    def __init__(self, minPos:tuple, maxPos:tuple, name_s:str, weight:float, initPos:Tuple[float, float, float],
                 static_b:bool, bouding_b:bool, blocking_b:bool, trigger_b:bool, triggerCommand_l:list, activateOption_i:int):
        ActorGeneral.__init__( self, name_s, static_b, initPos )

        x0, y0, z0 = minPos
        x1, y1, z1 = maxPos

        xS = x0 if x0 < x1 else x1
        yS = y0 if y0 < y1 else y1
        zS = z0 if z0 < z1 else z1

        xB = x0 if x0 >= x1 else x1
        yB = y0 if y0 >= y1 else y1
        zB = z0 if z0 >= z1 else z1

        self.__min = mm.Vec4(xS, yS, zS, 1)
        self.__max = mm.Vec4(xB, yB, zB, 1)

        self.__weight_f = float(weight)

        self.__bounding = bool(bouding_b)
        self.__blocking = bool(blocking_b)
        self.__trigger = bool(trigger_b)

        self.__triggerCommand_l = list(triggerCommand_l)

        self.activateOption_i = int(activateOption_i)
        self.lastState_b = False

    def __str__(self) -> str:
        return "< AABB object, min: {}, max: {} >".format(self.getWorldMinXYZ(None), self.getWorldMaxXYZ(None))

    def __getMaxXYZ(self) -> Tuple[float, float, float]:
        xMax_f, yMax_f, zMax_f = self.__max.getXYZ()
        xPos_f, yPos_f, zPos_f = self.getWorldXYZ()
        return xMax_f+xPos_f, yMax_f+yPos_f, zMax_f+zPos_f

    def __getMinXYZ(self) -> Tuple[float, float, float]:
        xMax_f, yMax_f, zMax_f = self.__min.getXYZ()
        xPos_f, yPos_f, zPos_f = self.getWorldXYZ()
        return xMax_f + xPos_f, yMax_f + yPos_f, zMax_f + zPos_f

    def getWorldMaxXYZ(self, parent:Optional["Actor"]) -> Tuple[float, float, float]:
        x,y,z = self.__getMaxXYZ()
        if parent is not None:
            xW,yW,zW = parent.getWorldXYZ()
            x += xW
            y += yW
            z += zW
        return x,y,z

    def getWorldMinXYZ(self, parent:Optional["Actor"]) -> Tuple[float, float, float]:
        x, y, z = self.__getMinXYZ()

        if parent is not None:
            xW, yW, zW = parent.getWorldXYZ()
            x += xW
            y += yW
            z += zW
        return x,y,z

    def getWeight(self) -> float:
        if self.getStatic():
            return 0.0
        else:
            return self.__weight_f

    def getTypes(self) -> Tuple[bool, bool, bool]:
        return self.__bounding, self.__blocking, self.__trigger

    def getTriggerCommands(self) -> List[str]:
        return self.__triggerCommand_l


class Segment(ActorGeneral):
    def __init__(self, name_s, static_b, initPos_t:Tuple[float, float, float], initVec:mm.Vec4):
        super().__init__(name_s, static_b, initPos_t)

        self.__vec = mm.Vec4(*initVec.getXYZ(), 0.0)

    def getSegmentPos(self, parent:Optional[Actor]) -> Tuple[float, float, float]:
        return self.getWorldXYZ(parent)

    def getSegmentDirection(self, parent:Optional[Actor]) -> Tuple[float, float, float]:
        if parent is None:
            return self.__vec.getXYZ()
        else:
            a = self.__vec.transform(self.getModelMatrix(parent)).getXYZ()
            return -a[0], -a[1], a[2]


def main():
    aabb = Aabb((-1, -1, -1), (1,1,1), "", 0.0, (0,0,0), False, True, False, False, [], 1)
    seg = Segment( "", False, (-2, 1.0, 0), mm.Vec4(4, 0, 0) )

    print(checkAabbSegment(aabb, None, seg, None))

if __name__ == '__main__':
    main()
