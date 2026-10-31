#version 450
// Pass 1 — Stage 3: vertical beam PSF convolution (energy-conserving) +
//          Stage 1.5: interlaced/progressive raster scan (field selection).
// Renders at viewport resolution so the sub-scanline beam profile is resolved.
// Input Source = linear beam current (Pass 0), sampled at source-row centres.
#include "params.inc"

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;   // true content resolution -> scanline count = .y
    vec4 SourceSize;
    uint FrameCount;     // for interlace field parity
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

#define MAX_RADIUS 3

void main()
{
    float rows = global.OriginalSize.y;        // source scanline count
    float sp   = vTexCoord.y * rows;           // fragment position in scanlines
    float sf   = fract(sp);
    int   si   = int(floor(sp));

    // Stage 1.5: raster scan mode. In interlaced (480i) only the current field's
    // scanlines are traced this frame; the other field's lines get I_b = 0 and
    // show their previous-field decaying glow via the Pass 4 feedback (flicker +
    // combing emerge for free). Progressive (240p) traces every line every frame.
    bool interlaced = (params.scan_mode > 1.5) ? (rows >= 400.0)    // 2 = auto
                                               : (params.scan_mode > 0.5); // 1 = force
    int field = int(global.FrameCount % 2u);

    // Stage 3b: oblique beam landing stretches the spot vertically toward the
    // screen edges. Same deflection angle theta that drives the brightness
    // falloff in the composite — one physical D_gun couples both.
    float st    = sin(deflection_theta(vTexCoord));
    float elong = 1.0 + params.k_edge * st * st;

    // Each SOURCE scanline deposits a unit-area Gaussian; weight from its own
    // beam current. Bright lines spread into dark neighbours, not vice versa.
    // In parallel we track a PEAK-normalized envelope (env = nearest line's
    // Gaussian, =1 on a line centre) — the pure geometric scanline shape,
    // independent of content — for the Stage 3c scanline-contrast power law.
    vec3  color = vec3(0.0);
    float env   = 0.0;
    float sig_e = params.sigma0 * elong;                     // envelope sigma (base, no space-charge)
    for (int i = -MAX_RADIUS; i <= MAX_RADIUS; i++) {
        int   line  = si + i;
        float src_y = (float(line) + 0.5) / rows;
        vec3  I_b   = texture(Source, vec2(vTexCoord.x, src_y)).rgb;  // already linear
        // Scanlines not in the current field dim to interlace_off instead of
        // black — modelling how consumer-TV phosphor persistence held the
        // previous field's glow, so real 480i/576i only flickered mildly.
        // (+2)%2 keeps parity correct for negative line indices near the top.
        if (interlaced && (((line % 2) + 2) % 2) != field) I_b *= params.interlace_off;
        float sigma = spot_sigma(dot(I_b, LUMA)) * elong;   // fatter toward edges
        float dy    = float(i) + 0.5 - sf;
        color += I_b * beam_weight(dy, sigma);
        env    = max(env, exp(-(dy * dy) / (2.0 * sig_e * sig_e)));   // peak-normalized
    }
    // Stage 3c: extra power-law on the scanline modulation. env==1 at the beam
    // centre (peak untouched, stays round); env<1 in the gap is pushed darker,
    // deepening the horizontal dark lines. scan_gamma==1 -> exponent 0 -> no-op.
    color *= pow(env, max(params.scan_gamma - 1.0, 0.0));
    FragColor = vec4(color, 1.0);
}
