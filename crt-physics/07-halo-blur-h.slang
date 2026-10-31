#version 450
#pragma name HaloH
// Pass 6 — Stage 6 halation, horizontal Gaussian blur at 1/4 res (separable).
// sigma is in this pass's texels: halo_spread is in full-viewport px and the pass
// runs at 1/4 res, so sigma_texels = halo_spread * 0.25 (must match the preset's
// 0.25 downscale). Weights are normalized (a blur preserves DC / brightness).
#include "params.inc"

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;
    vec4 SourceSize;   // HaloDown (1/4 res)
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
layout(set = 0, binding = 2) uniform sampler2D Source;   // HaloDown

#define R 12
#define DOWNSCALE 0.25

void main()
{
    float sigma = max(params.halo_spread * DOWNSCALE, 0.35);
    float tx = global.SourceSize.z;                       // one texel (x)
    vec3  acc = vec3(0.0);
    float wsum = 0.0;
    for (int i = -R; i <= R; i++) {
        float w = exp(-(float(i) * float(i)) / (2.0 * sigma * sigma));
        acc  += texture(Source, vTexCoord + vec2(float(i) * tx, 0.0)).rgb * w;
        wsum += w;
    }
    FragColor = vec4(acc / wsum, 1.0);
}
