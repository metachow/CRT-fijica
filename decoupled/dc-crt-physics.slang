#version 450
// =============================================================================
//  Decoupled CRT LAYER — PHYSICS edition.
//  Runs AFTER the full physics emission + halation chain (crt-physics passes
//  01..08). Instead of warping the FULL viewport (the old standalone
//  09-composite, removed), this applies the SHARED ScreenRect geometry (dc-screen-layout.inc)
//  so the curved CRT sits exactly in the bezel's screen hole — same curvature,
//  position and scale as the bezel/reflection. Output: display-referred, full
//  viewport, CRT inside the rect, black outside. dc-composite then draws the
//  bezel around it. The physics passes are reused UNCHANGED.
//
//  NOTE (quality): the physics chain bakes scanlines (passes 02/03) and the
//  phosphor mask (pass 04) at FULL-VIEWPORT resolution. Sampling that emission
//  into the smaller tube resamples those high-frequency features, which can
//  moiré (mask worst; scanlines borderline at 240p). A fully native-resolution
//  tube would require rendering the physics chain at tube scale — a larger
//  refactor gated by RA's compile-time framebuffer scale vs the runtime DC_*
//  params. This layer proves alignment; revisit the mask if moiré is visible.
// =============================================================================
layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;
    vec4 SourceSize;
    vec4 FinalViewportSize;
} global;

#include "dc-screen-layout.inc"

// physics composite knobs — baked here (crt-physics params.inc defaults). Promote
// to a merged push_constant later if per-preset tuning of these is wanted.
#define HALO_WEIGHT 0.04    // fraction of emitted light scattered by the glass
#define VIGNETTE    0.12    // edge brightness falloff (deflection cos law)
#define D_GUN       1.5     // gun-to-screen distance -> deflection angle

#pragma stage vertex
layout(location = 0) in vec4 Position;
layout(location = 1) in vec2 TexCoord;
layout(location = 0) out vec2 vTexCoord;
void main() { gl_Position = global.MVP * Position; vTexCoord = TexCoord; }

#pragma stage fragment
layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 FragColor;
layout(set = 0, binding = 2) uniform sampler2D Source;    // HaloV  (1/4 res, linear halation)
layout(set = 0, binding = 3) uniform sampler2D Persist;   // full-res linear emission

// sRGB encode (from crt-physics helpers.inc, inlined to avoid its params.* deps)
vec3 to_srgb(vec3 c){
    c = clamp(c, 0.0, 1.0);
    bvec3 hi = greaterThan(c, vec3(0.0031308));
    return mix(c * 12.92, 1.055 * pow(c, vec3(1.0/2.4)) - 0.055, vec3(hi));
}

void main()
{
    float out_aspect = global.OutputSize.x / global.OutputSize.y;
    ScreenRect r = dc_get_rect(out_aspect);
    float inside;
    vec2 sp = dc_vp_to_screen(vTexCoord, r, inside);      // curved content coord [0,1] in the tube

    // black well outside the rect (perf). Sampling CLAMPS at the edge so the
    // composite's anti-aliased screen-edge mask has real content to blend against
    // (no dark fringe).
    vec2 pflat = (vTexCoord - r.center) / r.half_size;
    if (abs(pflat.x) > 1.03 || abs(pflat.y) > 1.03) { FragColor = vec4(0.0); return; }

    // physics emission + glass halation, sampled at the content coordinate
    vec3 direct    = texture(Persist, sp).rgb;
    vec3 scattered = texture(Source,  sp).rgb;
    vec3 L = mix(direct, scattered, HALO_WEIGHT);

    // Stage 2d edge brightness falloff (deflection cos law), relative to content centre
    vec2  pc    = (sp - 0.5) * 2.0;
    float theta = atan(length(pc) / D_GUN);
    L *= mix(1.0, pow(max(cos(theta), 0.0), 2.5), VIGNETTE);

    // Display-referred out (matches the bezel's display-referred space). The rounded
    // screen-edge mask is applied ONCE by the composite pass, so it is omitted here.
    FragColor = vec4(to_srgb(L), 1.0);
}
