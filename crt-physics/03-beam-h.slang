#version 450
// Pass 2 — Stage 3: horizontal beam PSF convolution (energy-conserving).
// NEW vs. Phase 1: spreads each source column horizontally, so sub-triad-width
// vertical features are averaged across a full mask triad (fixes the colour
// fringing a 1-px vertical-line grid pattern otherwise shows).
// Input Source = BEAM_V (viewport res); offsets are in source-COLUMN units.
#include "params.inc"

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;   // true content resolution -> column count = .x
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

// Wider window than the vertical pass: the horizontal spot can be broadened well
// past 1 source pixel (bandwidth softening + space charge), so ±4 avoids truncation.
#define MAX_RADIUS 4

void main()
{
    float cols = global.OriginalSize.x;        // source column count
    float sp   = vTexCoord.x * cols;
    float sf   = fract(sp);
    int   si   = int(floor(sp));

    vec3 color = vec3(0.0);
    for (int i = -MAX_RADIUS; i <= MAX_RADIUS; i++) {
        float src_x = (float(si + i) + 0.5) / cols;
        vec3  s     = texture(Source, vec2(src_x, vTexCoord.y)).rgb;  // vertically-convolved, linear
        float sigma = spot_sigma_base(params.sigma_h, dot(s, LUMA));  // wider horizontal spot
        float dx    = float(i) + 0.5 - sf;
        color += s * beam_weight(dx, sigma);
    }
    FragColor = vec4(color, 1.0);
}
