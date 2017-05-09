#version 330 core


// In RenderingDude
uniform vec3 ambientLight;
uniform vec3 viewPos;

uniform int drawFlashLightShadow_i;
uniform int flashLightOn_i;
uniform vec3 flashLightPos;
uniform vec3 flashLightColor;
uniform vec3 flashLightDirection;
uniform float flashLightMaxDist_f;
uniform float flashLightCutoff_f;
uniform sampler2D flashLightShadowMap;

// In each object
uniform int selected_i;

// In each renderer
uniform sampler2D diffuseMap;
uniform float shininess;
uniform float specularStrength;

// In each level
uniform int pointLightCount;
uniform vec3 pointLightPos[10];
uniform vec3 pointLightColor[10];
uniform float pointLightMaxDistance[10];

in vec2 texCoordOut;
in vec3 normalVec;
in vec3 fragPos;
in vec4 fragPosFlashLightSpace;


out vec4 color;


vec3 accumPointLight(vec3 viewDir, vec3 curlightPos, vec3 curlightColor, float curlightMaxDistance)
{
    float distance_f = length(curlightPos - fragPos);
    vec3 lightDir = normalize(curlightPos - fragPos);
    float distanceDecreaser = -1 / (curlightMaxDistance*curlightMaxDistance) * (distance_f*distance_f) + 1;

    vec3 diffuse;
    if (distance_f > curlightMaxDistance)
    {
        diffuse = vec3(0.0);
    }
    else
    {
        float diff_f = max(dot(normalVec, lightDir), 0.0);
        diffuse = max(diff_f * curlightColor, vec3(0.0));
    }

    // Calculate specular lighting.
    if (shininess == 0.0)
    {
        return diffuse * distanceDecreaser;
    }
    else
    {
        vec3 reflectDir = reflect(-lightDir, normalVec);
        float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);

       // vec3 halfwayDir = normalize(lightDir + viewDir);
      //  spec = pow(max(dot(normalVec, halfwayDir), 0.0), 64.0);
        vec3 specular = max(specularStrength * spec * curlightColor, vec3(0.0));

        return diffuse * distanceDecreaser + specular;
    }
}


vec3 accumSpotLight(vec3 viewDir, vec3 curlightPos, vec3 curlightColor, vec3 curLightDirection, float curlightMaxDistance, float curLightCutoff)
{
    float distance_f = length(curlightPos - fragPos);
    vec3 lightDir = normalize(curlightPos - fragPos);
    float theta = dot(lightDir, normalize(-curLightDirection));

    if (theta > curLightCutoff)
        return accumPointLight(viewDir, curlightPos, curlightColor, curlightMaxDistance) * 10 *(theta - curLightCutoff);
    else
        return vec3(0.0);
}


float calculateFlashLightShadow(void)
{
    // perform perspective divide
    vec3 projCoords = fragPosFlashLightSpace.xyz / fragPosFlashLightSpace.w;
    if (projCoords.z > 1.0)
        return 0.0;
    // Transform to [0,1] range

    projCoords = projCoords * 0.5 + 0.5;
    if (projCoords.x < 0.0 || projCoords.x > 1.0 || projCoords.y < 0.0 || projCoords.y > 1.0)
        return 0.0;
    // Get closest depth value from light's perspective (using [0,1] range fragPosLight as coords)
    float closestDepth = texture(flashLightShadowMap, projCoords.xy).r;
    // Get depth of current fragment from light's perspective
    float currentDepth = projCoords.z;
    // Check whether current frag pos is in shadow
    vec3 lightDir = normalize(viewPos - fragPos);

    // float bias = max(0.05 * (1.0 - dot(normalVec, lightDir)), 0.005);
    float bias = 0.003;

    float shadow = 0.0;

    vec2 texelSize = 1.0 / textureSize(flashLightShadowMap, 0);
    for(int x = -1; x <= 1; ++x)
    {
        for(int y = -1; y <= 1; ++y)
        {
            float pcfDepth = texture(flashLightShadowMap, projCoords.xy + vec2(x, y) * texelSize).r;
            shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;
        }
    }
    shadow /= 9.0;

    return shadow;
}



void main(void)
{
    vec3 accumLight = ambientLight;
    vec3 viewDir = normalize(viewPos - fragPos);

    for (int i = 0; i < pointLightCount; i++)
    {
        accumLight += max( accumPointLight(viewDir, pointLightPos[i], pointLightColor[i], pointLightMaxDistance[i]), vec3(0.0) );
    }

    // Flash light


    if (flashLightOn_i > 0)
    {

        vec3 flashLight = max( accumSpotLight(viewDir, flashLightPos, flashLightColor, flashLightDirection, flashLightMaxDist_f, flashLightCutoff_f),
                               vec3(0.0)
                              );

        float shadow = 0.0;
        if (drawFlashLightShadow_i > 0)
            shadow = calculateFlashLightShadow();

        accumLight += flashLight * (1.0 - shadow);
    }

    color = texture(diffuseMap, texCoordOut) * vec4(accumLight, 1.0);
    if (selected_i > 0)
        color = vec4(1.0);

    //float depthValue = texture(flashLightShadowMap, texCoordOut).r;
    //color = vec4(vec3(depthValue), 1.0);
}