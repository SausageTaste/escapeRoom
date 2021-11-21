from time import time
from math import sin, cos, tan, pi, sqrt, acos
from typing import Tuple, Union

import numpy as np


class StaticObject(Exception):
    def __str__(self):
        return "This object is static, in other words, constant."


class Vec4:
    def __init__(self, x:float, y:float, z:float, w:float=1.0, static_b:bool=False):
        self.__x = float(x)
        self.__y = float(y)
        self.__z = float(z)
        self.__w = float(w)

        self.static_b = bool(static_b)

    ######## Magic methods ########

    def __str__(self) -> str:
        return "< {}.Vec4 object at 0x{:0>16X}, values: ({:0.2f}, {:0.2f}, {:0.2f}, {:0.2f}) >".\
               format(__name__, id(self), *self.getXYZW())

    def __repr__(self) -> str:
        if __name__ == '__main__':
            return "Vec4({}, {}, {}, {})".format(*self.getXYZW())
        else:
            return "{}.Vec4({}, {}, {}, {})".format(__name__, *self.getXYZW())

    def __add__(self, other:"Vec4") -> "Vec4":
        xSum_f = self.getX() + other.getX()
        ySum_f = self.getY() + other.getY()
        zSum_f = self.getZ() + other.getZ()
        wSum_f = self.getW() + other.getW()
        if wSum_f > 0.0:
            wSum_f = 1.0

        return Vec4(xSum_f, ySum_f, zSum_f, wSum_f)

    def __sub__(self, other:"Vec4") -> "Vec4":
        xSum_f = self.getX() - other.getX()
        ySum_f = self.getY() - other.getY()
        zSum_f = self.getZ() - other.getZ()
        wSum_f = self.getW() - other.getW()
        if wSum_f == -1:
            wSum_f = 1

        return Vec4(xSum_f, ySum_f, zSum_f, wSum_f)

    def __mul__(self, other:float) -> "Vec4":
        other = float(other)
        xNew_f = self.getX() * other
        yNew_f = self.getY() * other
        zNew_f = self.getZ() * other

        return Vec4(xNew_f, yNew_f, zNew_f, self.getW())

    ######## Getters and Setters or private attributes ########

    def getX(self) -> float:
        return self.__x

    def getY(self) -> float:
        return self.__y

    def getZ(self) -> float:
        return self.__z

    def getW(self) -> float:
        return self.__w

    def setX(self, x:float) -> None:
        if self.getStatic():
            raise StaticObject
        self.__x = float(x)

    def setY(self, y:float) -> None:
        if self.getStatic():
            raise StaticObject
        self.__y = float(y)

    def setZ(self, z:float) -> None:
        if self.getStatic():
            raise StaticObject
        self.__z = float(z)

    def setW(self, w:float) -> None:
        if self.getStatic():
            raise StaticObject
        self.__w = float(w)

    def getStatic(self):
        return self.static_b

    ######## Getters and Setters for convenience ########

    def getXYZ(self) -> Tuple[float, float, float]:
        return self.getX(), self.getY(), self.getZ()

    def getXYZW(self) -> Tuple[float, float, float, float]:
        return self.getX(), self.getY(), self.getZ(), self.getW()

    def setXYZ(self, x:float, y:float, z:float) -> None:
        self.setX(x)
        self.setY(y)
        self.setZ(z)

    def setXYZW(self, x:float, y:float, z:float, w:float) -> None:
        self.setX(x)
        self.setY(y)
        self.setZ(z)
        self.setW(w)

    ########  ########

    def copy(self) -> "Vec4":
        return Vec4(*self.getXYZW())

    def getLength(self) -> float:
        return sqrt(self.getX()**2 + self.getY()**2 + self.getZ()**2)

    def normalize(self) -> "Vec4":
        divider_f = self.getLength()
        if divider_f == 0:
            return Vec4(0,0,0)
        xNew_f = self.getX() / divider_f
        yNew_f = self.getY() / divider_f
        zNew_f = self.getZ() / divider_f

        return Vec4(xNew_f, yNew_f, zNew_f, 0.0)

    def cross(self, other:"Vec4") -> "Vec4":
        selfArray = np.array(self.getXYZ(), np.float32)
        otherArray = np.array(other.getXYZ(), np.float32)
        crossed = np.cross( selfArray, otherArray )
        return Vec4(crossed.item(0), crossed.item(1), crossed.item(2), 0.0)

    def cross3(self, other:"Vec4", theOther:"Vec4") -> "Vec4":
        v0 = other - self  # self -> other
        v1 = theOther - other  # other -> theOther
        return v0.cross(v1)

    def dot(self, other:"Vec4") -> float:
        selfArray = np.array(self.getXYZ(), np.float32)
        otherArray = np.array(other.getXYZ(), np.float32)
        scala_f = np.dot(selfArray, otherArray).item(0)
        return scala_f

    def getRadianDiff(self, other:"Vec4") -> float:
        radian_f = acos( self.dot(other) / (self.getLength() * other.getLength()) )
        return radian_f

    def getDegreeDiff(self, other:"Vec4") -> float:
        return self.getRadianDiff(other) *180/pi

    def getAngleDiff(self, other:"Vec4") -> "Angle":
        return Angle(self.getDegreeDiff(other))

    def transform(self, *args:np.ndarray) -> "Vec4":
        a = np.array([self.getXYZW()], np.float32)
        for tranMat in args:
            a = a.dot(tranMat)
        return Vec4(a.item(0), a.item(1), a.item(2), a.item(3))


class Angle:
    def __init__(self, degree_f:float, static_b:bool=False):
        self.__static_b = False

        self.__degree_f = None
        self.setDegree(degree_f)

        self.__static_b = bool(static_b)

    @classmethod
    def fromRadian(cls, radian_f:float) -> "Angle":
        return cls(radian_f*180/pi)

    def __str__(self) -> str:
        return "< {}.Angle object at 0x{:0>16X}, degree: {}, radian: {} >".format(
            __name__, id(self), self.getDegree(), self.getRadian()
        )

    def __repr__(self) -> str:
        if __name__ == '__main__':
            return "Angle({})".format(self.getDegree())
        else:
            return "{}.Angle({})".format(__name__, self.getDegree())

    def __add__(self, other:"Angle") -> "Angle":
        return Angle(self.getDegree() + other.getDegree())

    def __sub__(self, other:"Angle") -> "Angle":
        return Angle(self.getDegree() - other.getDegree())

    #### Only these uses attributes ####

    def getDegree(self) -> float:
        return self.__degree_f

    def setDegree(self, degree_f:Union[float, int]) -> None:
        degree_f = float(degree_f)

        if self.getStatic():
            raise StaticObject

        for _ in range(10000):
            if degree_f >= 360.0:
                degree_f -= 360.0
            elif degree_f < 0.0:
                degree_f += 360.0
            else:
                break
        else:
            raise ValueError("Too big value.")

        self.__degree_f = degree_f

    def getStatic(self) -> bool:
        return self.__static_b

    ####  ####

    def getRadian(self) -> float:
        return self.getDegree() / 180 * pi

    def setRadian(self, radian_f:Union[float, int]) -> None:
        self.setDegree(radian_f * 180 / pi)

    def setAngle(self, other:"Angle") -> None:
        self.setDegree(other.getDegree())

    def addDegree(self, degree_f:Union[float, int]) -> None:
        self.setDegree(self.getDegree() + degree_f)

    def addRadian(self, radian_f:Union[float, int]) -> None:
        self.setRadian(self.getRadian() + radian_f)

    def copy(self) -> "Angle":
        return Angle(self.__degree_f)


def getIdentityMat4() -> np.ndarray:
    return np.array([
        [ 1.0,  0.0,  0.0,  0.0 ],
        [ 0.0,  1.0,  0.0,  0.0 ],
        [ 0.0,  0.0,  1.0,  0.0 ],
        [ 0.0,  0.0,  0.0,  1.0 ]
    ], dtype=np.float32)

def getTranslateMat4(x:float, y:float, z:float, scala=1.0) -> np.ndarray:
    return np.array([
        [     1.0,      0.0,      0.0,  0.0 ],
        [     0.0,      1.0,      0.0,  0.0 ],
        [     0.0,      0.0,      1.0,  0.0 ],
        [ x*scala,  y*scala,  z*scala,  1.0 ]
    ], np.float32)

def getRotateXMat4(degree_f:float) -> np.ndarray:
    radian_f = degree_f / 180.0 * pi
    return np.array([
        [ 1.0,            0.0,             0.0,  0.0 ],
        [ 0.0,  cos(radian_f),  -sin(radian_f),  0.0 ],
        [ 0.0,  sin(radian_f),   cos(radian_f),  0.0 ],
        [ 0.0,            0.0,             0.0,  1.0 ]
    ], dtype=np.float32)

def getRotateYMat4(degree_f:float) -> np.ndarray:
    radian_f = degree_f / 180.0 * pi
    return np.array([
        [  cos(radian_f),  0.0,  sin(radian_f),  0.0 ],
        [            0.0,  1.0,            0.0,  0.0 ],
        [ -sin(radian_f),  0.0,  cos(radian_f),  0.0 ],
        [            0.0,  0.0,            0.0,  1.0 ]
    ], dtype=np.float32)

def getRotateZMat4(degree_f:float) -> np.ndarray:
    radian_f = degree_f / 180.0 * pi
    return np.array([
        [  cos(radian_f),  sin(radian_f),  0.0,  0.0 ],
        [ -sin(radian_f),  cos(radian_f),  0.0,  0.0 ],
        [            0.0,            0.0,  1.0,  0.0 ],
        [            0.0,            0.0,  0.0,  1.0 ]
    ], dtype=np.float32)

def getRotateXYZMat4(degree_f:float, x:float, y:float, z:float) -> np.ndarray:
    radian_f = degree_f / 180.0 * pi
    xa = radian_f * x
    ya = radian_f * y
    za = radian_f * z

    return np.array([
        [                           cos(ya)*cos(za),                           -cos(ya)*sin(za),             sin(ya),  0.0 ],
        [ cos(xa)*sin(za) + sin(xa)*sin(ya)*cos(za),  cos(xa)*cos(za) - sin(xa)*sin(ya)*sin(za),    -sin(xa)*cos(ya),  0.0 ],
        [ sin(xa)*sin(za) - cos(xa)*sin(ya)*cos(za),  sin(xa)*cos(za) + cos(xa)*sin(ya)*sin(za),     cos(xa)*cos(ya),  0.0 ],
        [                                       0.0,                                        0.0,                 0.0,  1.0 ]
    ], dtype=np.float32)

def getScaleMat4(x:float, y:float, z:float) -> np.ndarray:
    return np.array([
        [   x,  0.0,  0.0,  0.0 ],
        [ 0.0,    y,  0.0,  0.0 ],
        [ 0.0,  0.0,    z,  0.0 ],
        [ 0.0,  0.0,  0.0,  1.0 ]
    ], dtype=np.float32)

def getFrustumMat4(left:float, right:float, bottom:float, top:float, n:float, f:float) -> np.ndarray:
    if right == left or top == bottom or n == f or n < 0.0 or f < 0.0:
        return getIdentityMat4()

    return np.array([
        [2*n,  0,                         (right + left) / (right - left),  0                     ],
        [0,    (2 * n) / (top - bottom),  (top + bottom) / (top - bottom),  0                     ],
        [0,    0,                         (n + f) / (n - f),                (2 * n * f) / (n - f) ],
        [0,    0,                         -1,                               1                     ]
    ], dtype=np.float32)

def getPerspectiveMat4(fovDegree_f:float, aspect:float, n:float, f:float) -> np.ndarray:
    tanHalfFov_f = tan((fovDegree_f / 180 * pi) / 2)
    fSubN_f = f - n
    return np.array([
        [ 1.0 / (aspect * tanHalfFov_f),                 0.0,                             0.0,   0.0],
        [                           0.0,  1.0 / tanHalfFov_f,                             0.0,   0.0],
        [                           0.0,                 0.0,        -1.0 * (f + n) / fSubN_f,  -1.0],
        [                           0.0,                 0.0,  -1.0 * (2.0 * f * n) / fSubN_f,   0.0]
    ], dtype=np.float32)

def getOrthoMat4(l:float, r:float, b:float, t:float, n:float, f:float) -> np.ndarray:
    return np.array([
        [ 2.0 / (r - l),            0.0,            0.0,  0.0 ],
        [           0.0,      2 / (t-b),            0.0,  0.0 ],
        [           0.0,            0.0,    2.0 / (n-f),  0.0 ],
        [ (l+r) / (l-r),  (b+t) / (b-t),  (n+f) / (n-f),  1.0 ]
    ], dtype=np.float32)

def getlookatMat4(eye:Vec4, center:Vec4, up:Vec4) -> np.ndarray:
    f = (center - eye).normalize()
    upN = up.normalize()
    s = f.cross(upN)
    u = s.cross(f)
    return np.array([
        [s.getX(), u.getX(), -f.getX(), 0.0],
        [s.getY(), u.getY(), -f.getY(), 0.0],
        [s.getZ(), u.getZ(), -f.getZ(), 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ], np.float32)


def __timeIt():
    count_i = 500000

    st = time()
    for _ in range(count_i):
        tm1 = getRotateXYZMat4_2(1,2,3,4)
    print("tm1:", time() - st)

    st = time()
    for _ in range(count_i):
        tm2 = getRotateXYZMat4(1,2,3,4)
    print("tm2:", time() - st)

    print(tm1)
    print(tm2)

def __main():
    a = Angle(283)

    print(a)

if __name__ == '__main__':
    __main()
