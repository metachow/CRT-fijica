#version 450
// Pass 3 — Stage 4 (phosphor mask) + Stage 5a (saturation).
// Outputs LINEAR light (float framebuffer). The sRGB encode now lives in the
// final output pass; temporal decay (Pass 4) reads this linear emission.
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
layout(set = 0, binding = 2) uniform sampler2D Source;   // BEAM_HV, linear
#include "helpers.inc"

void main()
{
    vec3 e = texture(Source, vTexCoord).rgb;         // convolved linear beam energy

    // Stage 4: phosphor mask multiplies the beam result. Mask lives in OUTPUT-
    // pixel space, so use gl_FragCoord.xy (aperture grille uses x only; slot and
    // shadow masks add vertical structure from y).
    e *= phosphor_mask(gl_FragCoord.xy);

    // Stage 5a: per-channel saturation, applied AFTER masking. Normalized so a
    // reference drive of e=1 maps to L=1 (restores the dropped efficiency
    // constant); only super-unity drive — where the mask concentrates energy —
    // rolls off. This keeps normal signal from being dimmed by the knee.
    vec3 L = e * (1.0 + 1.0 / params.e_sat) / (1.0 + e / params.e_sat);

    // Emission gain (η_0): compensates the brightness the mask removes so
    // calibrated white reaches full output. Highlights above 1 bloom to white.
    L *= params.brightness;

    // Emit linear light; encode happens in the final output pass.
    FragColor = vec4(L, 1.0);
}
