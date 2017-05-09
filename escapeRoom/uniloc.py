import OpenGL.GL as gl


class UniformLocs:
    def __init__(self, program:int):
        # In vertex shader

        self.projectionMatrix = gl.glGetUniformLocation(program, "projectionMatrix")
        self.viewMatrix = gl.glGetUniformLocation(program, "viewMatrix")
        self.flashLightSpaceMatrix = gl.glGetUniformLocation(program, "flashLightSpaceMatrix")

        self.modelMatrix = gl.glGetUniformLocation(program, "modelMatrix")
        self.textureVerNum_f = gl.glGetUniformLocation(program, "textureVerNum_f")
        self.textureHorNum_f = gl.glGetUniformLocation(program, "textureHorNum_f")

        # In fragment shader

        self.ambientLight = gl.glGetUniformLocation(program, "ambientLight")
        self.viewPos = gl.glGetUniformLocation(program, "viewPos")

        self.drawFlashLightShadow_i = gl.glGetUniformLocation(program, "drawFlashLightShadow_i")
        self.flashLightOn_i = gl.glGetUniformLocation(program, "flashLightOn_i")
        self.flashLightPos = gl.glGetUniformLocation(program, "flashLightPos")
        self.flashLightColor = gl.glGetUniformLocation(program, "flashLightColor")
        self.flashLightDirection = gl.glGetUniformLocation(program, "flashLightDirection")
        self.flashLightMaxDist_f = gl.glGetUniformLocation(program, "flashLightMaxDist_f")
        self.flashLightCutoff_f = gl.glGetUniformLocation(program, "flashLightCutoff_f")
        self.flashLightShadowMap = gl.glGetUniformLocation(program, "flashLightShadowMap")

        self.selected_i = gl.glGetUniformLocation(program, "selected_i")

        self.diffuseMap = gl.glGetUniformLocation(program, "diffuseMap")
        self.shininess = gl.glGetUniformLocation(program, "shininess")
        self.specularStrength = gl.glGetUniformLocation(program, "specularStrength")

        self.pointLightCount = gl.glGetUniformLocation(program, "pointLightCount")
        self.pointLightPos = gl.glGetUniformLocation(program, "pointLightPos")
        self.pointLightColor = gl.glGetUniformLocation(program, "pointLightColor")
        self.pointLightMaxDistance = gl.glGetUniformLocation(program, "pointLightMaxDistance")


class UniformLocsOverlay:
    def __init__(self, program:int):
        # In vertex shader

        self.leftUpperCoord = gl.glGetUniformLocation(program, "leftUpperCoord")
        self.rightDownCoord = gl.glGetUniformLocation(program, "rightDownCoord")

        self.diffuseMap_b = gl.glGetUniformLocation(program, "diffuseMap_b")
        self.maskMap_i = gl.glGetUniformLocation(program, "maskMap_i")

        self.diffuseMap = gl.glGetUniformLocation(program, "diffuseMap")
        self.maskMap = gl.glGetUniformLocation(program, "maskMap")

        self.diffuseColor = gl.glGetUniformLocation(program, "diffuseColor")
        self.baseMask_f = gl.glGetUniformLocation(program, "baseMask_f")


        a = dir(self)
        for x in a:
            if x.endswith("__"):
                continue
            if getattr(self, x) < 0:
                raise ValueError(x)