#version 330 core


uniform vec2 leftUpperCoord;
uniform vec2 rightDownCoord;


out vec2 texCoordOut;


vec2 getPosition(int vertexIndex_i)
{
    vec2 result = vec2(0.0);

    switch (vertexIndex_i)
    {
    case 0:
        result = vec2( leftUpperCoord.x, leftUpperCoord.y );
        break;
    case 1:
        result = vec2( leftUpperCoord.x, rightDownCoord.y );
        break;
    case 2:
        result = vec2( rightDownCoord.x, rightDownCoord.y );
        break;
    case 3:
        result = vec2( leftUpperCoord.x, leftUpperCoord.y );
        break;
    case 4:
        result = vec2( rightDownCoord.x, rightDownCoord.y );
        break;
    case 5:
        result = vec2( rightDownCoord.x, leftUpperCoord.y );
        break;
    default:
        result = vec2(0.0);
    }

    return result;
}


vec2 getTexCoord(int vertexIndex_i)
{
    vec2 result = vec2(0.0);

    switch (vertexIndex_i)
    {
    case 0:
        result = vec2( 0.0, 1.0 );
        break;
    case 1:
        result = vec2( 0.0, 0.0 );
        break;
    case 2:
        result = vec2( 1.0, 0.0 );
        break;
    case 3:
        result = vec2( 0.0, 1.0 );
        break;
    case 4:
        result = vec2( 1.0, 0.0 );
        break;
    case 5:
        result = vec2( 1.0, 1.0 );
        break;
    default:
        result = vec2(0.0);
    }

    return result;
}


void main(void)
{
    gl_Position = vec4( getPosition(gl_VertexID), 0.0, 1.0 );
    texCoordOut = getTexCoord(gl_VertexID);
}