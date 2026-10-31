#version 450
#pragma name HaloDown
// Pass 5 — Stage 6 (halation) downsample. Reads the persisted linear emission and
// box-downsamples it to 1/4 viewport for the cheap wide blur that follows. Four
// bilinear taps at ±1 source-texel cover a 4x4 block (16 samples) so thin bright
// features still contribute to the glow.
#include "params.inc"

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;
    vec4 SourceSize;   // Persist (full res)
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
layout(set = 0, binding = 2) uniform sampler2D Source;   // Persist, linear, full res

void main()
{
    vec2 t = global.SourceSize.zw;                       // one full-res texel
    vec3 c = texture(Source, vTexCoord + vec2(-t.x, -t.y)).rgb
           + texture(Source, vTexCoord + vec2( t.x, -t.y)).rgb
           + texture(Source, vTexCoord + vec2(-t.x,  t.y)).rgb
           + texture(Source, vTexCoord + vec2( t.x,  t.y)).rgb;
    FragColor = vec4(c * 0.25, 1.0);
}
