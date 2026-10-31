#version 450
// =============================================================================
//  Decoupled FOREGROUND pass — the "in front of the glass" layer. Runs LAST, after
//  dc-composite: samples its output and alpha-composites the Foreground image on top
//  (device logo / LEDs / control panel — the parts that must sit OVER the bezel).
//  Gated by DC_FG_ON. This is also where AMBIENT lighting + room-glass reflection will
//  live later, since they're all "in front of the glass". Keeps dc-composite focused on
//  the physical tube + bezel + reflection + background.
//
//  Layer model (matches tools/crt-studio.html): Background (dc-composite) -> CRT+bezel
//  (dc-composite) -> Foreground (here). The Foreground image's screen area is transparent
//  so the tube shows; its logo/LED/panel are opaque and draw over everything.
// =============================================================================
layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;
    vec4 SourceSize;
    vec4 FinalViewportSize;
} global;

#include "dc-screen-layout.inc"   // shares the DC_* push_constant (uses DC_FG_ON)

#pragma stage vertex
layout(location = 0) in vec4 Position;
layout(location = 1) in vec2 TexCoord;
layout(location = 0) out vec2 vTexCoord;
void main() { gl_Position = global.MVP * Position; vTexCoord = TexCoord; }

#pragma stage fragment
layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 FragColor;
layout(set = 0, binding = 2) uniform sampler2D Source;      // dc-composite output (tube+bezel+bg)
layout(set = 0, binding = 3) uniform sampler2D Foreground;  // logo / LEDs / panel — over the glass

void main()
{
    vec3 base = texture(Source, vTexCoord).rgb;
    if (dcp.DC_FG_ON > 0.5) {
        vec4 fg = texture(Foreground, vTexCoord);   // straight alpha
        base = mix(base, dc_light(fg.rgb, vec3(0.0)), fg.a);   // pre-lit art -> under the room light
    }
    FragColor = vec4(base, 1.0);
}
