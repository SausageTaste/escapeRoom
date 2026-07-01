import OpenGL.GL as gl


class CompileErrorGLSL(Exception):
    def __init__(self, text_s:str):
        super().__init__(text_s)
        self.text_s = text_s

    def __str__(self):
        return self.text_s


def _decodeLog(log) -> str:
    if isinstance(log, bytes):
        return log.decode("utf8", errors="replace")
    return str(log)


def _compileShader(shaderType_i:int, shaderDir_s:str) -> int:
    shader = gl.glCreateShader(shaderType_i)
    with open(shaderDir_s) as file:
        gl.glShaderSource(shader, file.read())
    gl.glCompileShader(shader)

    if not gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS):
        log_s = _decodeLog(gl.glGetShaderInfoLog(shader)).strip()
        raise CompileErrorGLSL(f"{shaderDir_s}\n{log_s}")

    return shader


def getProgram(vertexShaderDir_s:str, fragmentShaderDir_s:str) -> int:
    vertexShader = _compileShader(gl.GL_VERTEX_SHADER, vertexShaderDir_s)
    fragmentShader = _compileShader(gl.GL_FRAGMENT_SHADER, fragmentShaderDir_s)

    program = gl.glCreateProgram()
    gl.glAttachShader(program, vertexShader)
    gl.glAttachShader(program, fragmentShader)
    gl.glLinkProgram(program)
    if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
        log_s = _decodeLog(gl.glGetProgramInfoLog(program)).strip()
        raise CompileErrorGLSL(f"{vertexShaderDir_s}, {fragmentShaderDir_s}\n{log_s}")

    gl.glDeleteShader(vertexShader)
    gl.glDeleteShader(fragmentShader)

    gl.glUseProgram(program)

    return int(program)
