from typing import Dict

import numpy as np


def parseObj(fileDir_s:str) -> Dict[ str, "OneRenderer" ]:
    fileData_d = {}
    resultData_d = {}

    with open(fileDir_s) as file:
        curObj_s = "noname"
        resultData_d[curObj_s] = OneRenderer()
        resultData_d[curObj_s].name_s = curObj_s

        for x_s in file:
            x_s = x_s.rstrip('\n')

            if x_s.startswith("o "):
                curObj_s = x_s.split()[1]
                if curObj_s in fileData_d:
                    raise FileExistsError
                resultData_d[curObj_s] = OneRenderer()
                resultData_d[curObj_s].name_s = curObj_s

            elif x_s.startswith("v "):
                if "v" not in fileData_d:
                    fileData_d["v"] = []
                _, x, y, z = x_s.split()
                fileData_d["v"].append((float(x), float(y), float(z)))
                del _, x, y, z
            elif x_s.startswith("vt "):
                if "vt" not in fileData_d:
                    fileData_d["vt"] = []
                _, x, y = x_s.split()
                fileData_d["vt"].append((float(x), float(y)))
                del _, x, y
            elif x_s.startswith("vn "):
                if "vn" not in fileData_d:
                    fileData_d["vn"] = []
                _, x, y, z = x_s.split()
                fileData_d["vn"].append((float(x), float(y), float(z)))
                del _, x, y, z

            elif x_s.startswith("usemtl "):
                resultData_d[curObj_s].mtl_s = x_s.split()[1]
            elif x_s.startswith("f "):
                _, v0_s, v1_s, v2_s = x_s.split()
                verticesIndices_t = (
                    tuple(map(lambda xx:int(xx), v0_s.split('/'))),
                    tuple(map(lambda xx:int(xx), v1_s.split('/'))),
                    tuple(map(lambda xx:int(xx), v2_s.split('/')))
                )

                for v_l in verticesIndices_t:
                    try:
                        resultData_d[curObj_s].vertices_l.append(fileData_d["v"][v_l[0] - 1])
                    except IndexError:
                        print("{}: {}, {}, v  <<  {}".format(curObj_s, v_l[0] - 1, len(fileData_d["v"]), repr(x_s)))
                    try:
                        resultData_d[curObj_s].texCoords_l.append(fileData_d["vt"][v_l[1] - 1])
                    except IndexError:
                        print("{}: {}, {}, vt  <<  {}".format(curObj_s, v_l[1] - 1, len(fileData_d["vt"]), repr(x_s)))
                    try:
                        resultData_d[curObj_s].normals_l.append(fileData_d["vn"][v_l[2] - 1])
                    except IndexError:
                        print("{}: {}, {}, vn  <<  {}".format(curObj_s, v_l[2] - 1, len(fileData_d["vn"]), repr(x_s)))

    del fileData_d["v"]
    del fileData_d["vt"]
    del fileData_d["vn"]

    for x in fileData_d:
        aa = fileData_d[x]
        assert len(aa["vt_i"]) == len(aa["vn_i"]) == len(aa["v_i"])
        del x, aa

    #### Make numpy array ####

    del resultData_d["noname"]

    for objName_s in resultData_d.keys():
        localObj_d = resultData_d[objName_s]  # Dictionary that contains vertex data atm. Local variable.

        #### Numpy ####

        localObj_d.vertexNdarray = np.array(localObj_d.vertices_l, dtype=np.float32)
        localObj_d.vertexNumber_i = localObj_d.vertexNdarray.size // 3

        localObj_d.textureCoordNdarray = np.array(localObj_d.texCoords_l, dtype=np.float32)

        localObj_d.normalNdarray = np.array(localObj_d.normals_l, dtype=np.float32)

        assert (localObj_d.vertexNdarray.size // 3) == (localObj_d.textureCoordNdarray.size // 2)
        assert (localObj_d.textureCoordNdarray.size // 2) == (localObj_d.normalNdarray.size // 3)

        localObj_d.vertices_l = None
        localObj_d.texCoords_l = None
        localObj_d.normals_l = None

        localObj_d.checkIntegrity()

    return resultData_d


def parseMtl(fileDir_s:str) -> Dict[ str, "OneMaterial" ]:
    materials_d = {}

    with open(fileDir_s) as file:
        curMat_s = ""
        for x, x_s in enumerate(file):
            x_s = x_s.strip('\n')

            if x_s.startswith("newmtl "):
                curMat_s = x_s.split()[1]
                if curMat_s in materials_d.keys():
                    raise FileExistsError
                materials_d[curMat_s] = OneMaterial()
                materials_d[curMat_s].name_s = curMat_s


            elif x_s.startswith("map_Kd "):
                materials_d[curMat_s].map_Kd_s = x_s.split()[1]

    for name_s in materials_d.keys():
        oneMaterial = materials_d[name_s]
        oneMaterial.checkIntegrity()

    return materials_d


class OneRenderer:
    def __init__(self):
        self.name_s = None

        self.vertices_l = []
        self.texCoords_l = []
        self.normals_l = []

        self.vertexNdarray = None
        self.textureCoordNdarray = None
        self.normalNdarray = None

        self.vertexNumber_i = None
        self.mtl_s = None

    def __repr__(self):
        return "< {}.OneRenderer object at 0x{:0>16X}, name: {}, vertexNumber: {}, mtl: {} >".format(
            __name__, id(self), self.name_s, self.vertexNumber_i, self.mtl_s
        )

    def checkIntegrity(self) -> None:
        if self.name_s is None:
            raise ValueError("name_s is not filled.")
        elif self.vertexNdarray is None:
            raise ValueError("vertexNdarray is not filled.")
        elif self.textureCoordNdarray is None:
            raise ValueError("textureCoordNdarray is not filled.")
        elif self.normalNdarray is None:
            raise ValueError("normalNdarray is not filled.")
        elif self.mtl_s is None:
            raise ValueError("mtl_s is not filled: {}".format(self.name_s))


class OneMaterial:
    def __init__(self):
        self.name_s = None
        self.map_Kd_s = None

    def __repr__(self):
        return "< {}.OneMaterial object at 0x{:0>16X}, name: {}, map_Kd: {} >".format(
            __name__, id(self), self.name_s, self.map_Kd_s
        )

    def checkIntegrity(self) -> None:
        if self.name_s is None:
            raise ValueError("name_s is not filled")
        elif self.map_Kd_s is None:
            raise ValueError("map_Kd_s is not filled")


def main():
    a = parseObj("C:\\Users\\sungmin\\OneDrive\\Programming\\Python\\3.5\\escapeRoom\\assets\\models\\palanquin.obj")
    b = parseMtl("C:\\Users\\sungmin\\OneDrive\\Programming\\Python\\3.5\\escapeRoom\\assets\\models\\palanquin.mtl")

    print(a)
    print(b)

    for x in a:
        print(a[x])

    for x in b:
        print(b[x])


if __name__ == '__main__':
    main()
