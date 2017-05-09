import OpenGL.GL as gl


class UniformLocsShadow:
    def __init__(self, program:int):
        # In vertex shader

        self.lightProjectMat = gl.glGetUniformLocation(program, "lightProjectMat")
        self.modelMat = gl.glGetUniformLocation(program, "modelMat")