#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec2 texCoord;
layout (location = 2) in vec3 normal;

// From Rendering dude
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;
uniform mat4 flashLightSpaceMatrix;

// From each renderer
uniform mat4 modelMatrix;
uniform float textureVerNum_f;
uniform float textureHorNum_f;


out vec2 texCoordOut;
out vec3 normalVec;
out vec3 fragPos;
out vec4 fragPosFlashLightSpace;






void main(void)
{
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
    texCoordOut = vec2(texCoord.x * textureHorNum_f, texCoord.y * textureVerNum_f);
    normalVec = normalize(vec3(modelMatrix * vec4(normal,   0.0)));
    fragPos = vec3(modelMatrix * vec4(position, 1.0));
    fragPosFlashLightSpace = flashLightSpaceMatrix * vec4(fragPos, 1.0);
}