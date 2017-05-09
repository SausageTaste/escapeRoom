#version 330 core


uniform int diffuseMap_b;
uniform int maskMap_i;

uniform sampler2D diffuseMap;
uniform sampler2D maskMap;

uniform vec3 diffuseColor;
uniform float baseMask_f;


in vec2 texCoordOut;


out vec4 color;


void main(void)
{
    float mask_f;
    if (maskMap_i > 0)
        mask_f = texture(maskMap, texCoordOut).r;
    else
        mask_f = baseMask_f;

    vec4 diffuse;
    if (diffuseMap_b > 0)
        diffuse = texture( diffuseMap, texCoordOut );
    else
        diffuse = vec4( diffuseColor, 1.0 );

    color = vec4( diffuse.rgb, diffuse.a * mask_f );
}