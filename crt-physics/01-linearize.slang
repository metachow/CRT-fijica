#version 450
// Pass 0 — Stage 1: signal decode & gun response.
// Output: linear per-channel beam current (rgba16f), at source resolution.
#include "params.inc"

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;
    vec4 SourceSize;
} global;

#pragma stage vertex
layout(location = 0) in vec4 Position;
layout(location = 1) in vec2 TexCoord;
layout(location = 0) out vec2 vTexCoord;
void main()
{
    gl_Position = global.MVP * Position;
    vTexCoord = TexCoord;
}

#pragma stage fragment
layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 FragColor;
layout(set = 0, binding = 2) uniform sampler2D Source;
#include "helpers.inc"

void main()
{
    vec3 I_b = gun_response(texture(Source, vTexCoord).rgb);
    FragColor = vec4(I_b, 1.0);
}
