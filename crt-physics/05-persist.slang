#version 450
#pragma name Persist
// Pass 4 — Stage 5b: phosphor temporal decay (afterglow), IIR feedback.
//
// Physics (Kuhn 2002 / EIA phosphor classification):
//   - Red (Y2O2S:Eu): pure exponential, fully decayed between frames -> NO
//     inter-frame persistence. persist_R = emission_R.
//   - Green (ZnS:Cu,Al) & Blue (ZnS:Ag,Cl): power-law tail (t+a)^-b survives
//     frame-to-frame -> visible afterglow. Green persists longest, giving the
//     characteristic greenish-cyan trailing; blue slightly shorter; red absent.
//
// Implementation: per-channel "hold-and-decay" IIR on the linear phosphor
// emission, persisted = max(emission, previous_persist * decay). A constant
// per-frame decay factor approximates the power-law tail over the first few
// (visually significant) frames — a practical approximation. This also smooths brightness transitions (a fading
// image holds its brighter, softer-spot rendering and decays gradually instead
// of snapping to the sharp low-current spot each frame).
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
layout(set = 0, binding = 2) uniform sampler2D Source;          // PHOSPHOR, linear
layout(set = 0, binding = 3) uniform sampler2D PersistFeedback; // previous frame's Persist

void main()
{
    vec3 emission = texture(Source, vTexCoord).rgb;          // linear this-frame emission
    vec3 prev     = texture(PersistFeedback, vTexCoord).rgb; // linear last-frame persisted

    // Per-channel afterglow decay. Red is small by default (physically fastest),
    // but tunable so a white object can leave a whiter tail instead of green/cyan.
    vec3 decay = vec3(params.persist_r, params.persist_g, params.persist_b);

    // Hold the brighter of the fresh emission or the decayed previous glow.
    vec3 persisted = max(emission, prev * decay);

    FragColor = vec4(persisted, 1.0);
}
