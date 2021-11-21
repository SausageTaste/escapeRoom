import OpenGL.GL as gl


class CompileErrorGLSL(Exception):
    def __init__(self, text_s:str):
        self.text_s = text_s

    def __str__(self):
        return self.text_s


def getProgram(vertexShaderDir_s:str, fragmentShaderDir_s:str) -> int:
    vertexShader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    with open(vertexShaderDir_s) as file:
        gl.glShaderSource(vertexShader, file.read())
    gl.glCompileShader(vertexShader)
    log_s = gl.glGetShaderInfoLog(vertexShader)
    if log_s:
        raise CompileErrorGLSL(log_s)

    fragmentShader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
    with open(fragmentShaderDir_s) as file:
        gl.glShaderSource(fragmentShader, file.read())
    gl.glCompileShader(fragmentShader)
    log_s = gl.glGetShaderInfoLog(fragmentShader)
    if log_s:
        raise CompileErrorGLSL(log_s)

    program = gl.glCreateProgram()
    gl.glAttachShader(program, vertexShader)
    gl.glAttachShader(program, fragmentShader)
    gl.glLinkProgram(program)

    gl.glDeleteShader(vertexShader)
    gl.glDeleteShader(fragmentShader)

    gl.glUseProgram(program)

    return int(program)
