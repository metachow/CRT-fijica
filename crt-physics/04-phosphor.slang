#version 450
#pragma name Persist
// Pass 3 — Stage 4 (phosphor mask) + Stage 5a (saturation) + Stage 5b (persistence).
// One pass, because all three are per pixel: no full-resolution intermediate between them.
// Outputs LINEAR light (float framebuffer); the sRGB encode lives in the final pass.
//
// Persistence physics (Kuhn 2002 / EIA phosphor classification):
//   - Red (Y2O2S:Eu): pure exponential, fully decayed between frames -> NO
//     inter-frame persistence.
//   - Green (ZnS:Cu,Al) & Blue (ZnS:Ag,Cl): power-law tail (t+a)^-b survives
//     frame-to-frame -> visible afterglow. Green persists longest, giving the
//     characteristic greenish-cyan trailing; blue slightly shorter; red absent.
//
// Implementation: an energy-conserving IIR, one feedback buffer per channel.
//     out = (1 - d) * emission + d * out_prev
// A frame's light shows (1 - d) at once and the rest as a tail d, d^2, ... that
// ADDS to whatever is drawn later (a trail stays visible over a bright
// background), while a still image keeps exactly its brightness (sum = 1). This
// equals 'prompt emission + separate tail buffer' with the tail weight tied to the
// decay, without a second buffer. A constant per-frame d approximates the
// power-law tail over the first few (visually significant) frames.
// persist_* is the decay per frame at 60 Hz; d is rescaled to the real refresh
// (content fps x subframes), so PAL 50 Hz or subframe BFI keep the same glow time.
#include "params.inc"

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;
    vec4 SourceSize;
    float OriginalFPS;     // content refresh rate (0 on old RetroArch builds -> 60 assumed)
    uint TotalSubFrames;   // shader subframes per content frame (1 = off)
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
layout(set = 0, binding = 2) uniform sampler2D Source;          // BEAM_HV: convolved linear beam energy
layout(set = 0, binding = 3) uniform sampler2D PersistFeedback; // previous frame's output of this pass
#include "helpers.inc"

void main()
{
    // Stage 4: the phosphor mask multiplies the beam result. It lives in OUTPUT-pixel space
    // (aperture grille uses x only; slot and shadow masks add vertical structure from y).
    vec3 e = texture(Source, vTexCoord).rgb * phosphor_mask(gl_FragCoord.xy);

    // Stage 5a: per-channel saturation, AFTER masking. Normalised so a reference drive of e=1
    // maps to 1; only super-unity drive (where the mask concentrates energy) rolls off.
    // Then the emission gain (η_0), which compensates the light the mask removes.
    vec3 emission = e * (1.0 + 1.0 / params.e_sat) / (1.0 + e / params.e_sat) * params.brightness;

    // Stage 5b: per-channel decay per 60 Hz frame, rescaled to the frames actually rendered;
    // the prompt part of this frame's light + the tail of all earlier frames.
    float fps   = ((global.OriginalFPS > 1.0) ? global.OriginalFPS : 60.0) * float(max(global.TotalSubFrames, 1u));
    vec3  decay = pow(clamp(vec3(params.persist_r, params.persist_g, params.persist_b), 0.0, 0.999), vec3(60.0 / fps));
    vec3  prev  = texture(PersistFeedback, vTexCoord).rgb;
    FragColor = vec4((1.0 - decay) * emission + decay * prev, 1.0);
}
