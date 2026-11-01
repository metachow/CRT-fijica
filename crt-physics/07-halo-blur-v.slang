#version 450
#pragma name HaloV
// Pass 6 — Stage 6 halation, vertical Gaussian blur at 1/4 res (separable).
// Completes the wide 2D glass-scatter Gaussian started in the horizontal pass.
#include "params.inc"

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;
    vec4 SourceSize;   // HaloH (1/4 res)
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
layout(set = 0, binding = 2) uniform sampler2D Source;   // HaloH

#define R 12
#define DOWNSCALE 0.25

void main()
{
    float sigma = max(params.halo_spread * DOWNSCALE, 0.35);
    float ty = global.SourceSize.w;                       // one texel (y)
    vec3  acc = vec3(0.0);
    float wsum = 0.0;
    for (int i = -R; i <= R; i++) {
        float w = exp(-(float(i) * float(i)) / (2.0 * sigma * sigma));
        acc  += texture(Source, vTexCoord + vec2(0.0, float(i) * ty)).rgb * w;
        wsum += w;
    }
    FragColor = vec4(acc / wsum, 1.0);
}
