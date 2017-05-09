import OpenGL.GL as gl


class BufferManager:
    def __init__(self):
        self.__vertexArrays_l = []
        self.__buffers_l = []

    def requestVertexArray(self) -> int:
        if len(self.__vertexArrays_l) > 0:
            vaoId_i = self.__vertexArrays_l.pop()
        else:
            vaoId_i = int( gl.glGenVertexArrays(1) )

        return vaoId_i

    @staticmethod
    def dumpVertexArray(vaoId_i:int) -> None:
        gl.glDeleteVertexArrays( 1, (vaoId_i,) )

    def requestBuffer(self) -> int:
        if len(self.__buffers_l) > 0:
            bufferId_i = self.__buffers_l.pop()
        else:
            bufferId_i = int( gl.glGenBuffers(1) )

        return bufferId_i

    def dumpBuffer(self, bufferId_i:int) -> None:
        self.__buffers_l.append(bufferId_i)
