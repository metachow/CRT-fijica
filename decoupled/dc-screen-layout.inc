// =============================================================================
//  dc-screen-layout.inc — THE CONTRACT shared by the CRT, bezel and reflection
//  passes of the decoupled bezel architecture.
//
//  The three modules never include each other; they all include THIS. It owns:
//    * the ScreenRect (where the emulated screen sits in the viewport),
//    * curvature/corner (shared, so scanlines/frame/reflection bend identically),
//    * viewport<->screen coordinate mapping.
//
//  The contract is carried by #pragma parameters (identical in every pass), so
//  each pass reconstructs the SAME rect with get_screen_rect(). No layout texture
//  round-trip needed; the params ARE the shared state. A fuller system could add
//  a Layout pass that derives these from OriginalSize/rotation and bakes them to
//  a 1x1 texture — the consumers below would then read that instead. The rest of
//  the architecture is unchanged.
//
//  Requires: `global` UBO with vec4 FinalViewportSize (declared by each pass).
// =============================================================================

layout(push_constant) uniform DCLayoutPush
{
    float DC_SCALE;    // screen height as fraction of viewport height
    float DC_POS_X;    // screen centre X in viewport [0,1]
    float DC_POS_Y;    // screen centre Y in viewport [0,1]
    float DC_ASPECT;   // content aspect ratio (w/h), e.g. 1.333 for 4:3
    float DC_CURVE_X;  // faceplate curving across the width (bows the top/bottom edges; 0 = flat)
    float DC_CURVE_Y;  // faceplate curving top to bottom (bows the left/right edges)
    float DC_CORNER;   // shared corner radius (screen-relative)
    float DC_BG_ON;    // 0 = procedural dark bg beyond the frame; 1 = sample Background image
    float DC_FG_ON;    // 0 = no foreground overlay; 1 = sample Foreground image (dc-foreground)
    float DC_ROOM_LIGHT;  // room light: 0 lights off (only the TV) . 0.5 a lamp at night . 1 daytime
    float DC_ROOM_TEMP;   // room light colour temperature, K (used when DC_ROOM_TYPE = 0)
    float DC_ROOM_TYPE;   // light source: 0 custom (DC_ROOM_TEMP) . 1 bulb . 2 fluorescent tube . 3 daylight
    float DC_SPILL;       // TV light spilling onto the bezel / frame
    float DC_GLASS_LIFT;  // room light reflected off the tube glass (greys the blacks in a lit room)
} dcp;

#pragma parameter DC_SCALE   "Layout: screen scale"     0.72  0.20 1.00 0.002
#pragma parameter DC_POS_X   "Layout: screen pos X"     0.50  0.00 1.00 0.001
#pragma parameter DC_POS_Y   "Layout: screen pos Y"     0.50  0.00 1.00 0.001
#pragma parameter DC_ASPECT  "Layout: content aspect"   1.333 0.50 2.50 0.001
#pragma parameter DC_CURVE_X "Layout: curvature X"      0.015 0.00 0.40 0.005
#pragma parameter DC_CURVE_Y "Layout: curvature Y"      0.025 0.00 0.40 0.005
#pragma parameter DC_CORNER  "Layout: corner radius"    0.018 0.00 0.15 0.002
#pragma parameter DC_BG_ON   "Layout: background image on"  0.0 0.0 1.0 1.0
#pragma parameter DC_FG_ON   "Layout: foreground image on"  0.0 0.0 1.0 1.0
#pragma parameter DC_ROOM_LIGHT "Light: room (0 off, 0.5 lamp, 1 day)" 1.0 0.0 1.0 0.01
#pragma parameter DC_ROOM_TYPE  "Light: source (0 custom K, 1 bulb, 2 fluorescent, 3 daylight)" 0.0 0.0 3.0 1.0
#pragma parameter DC_ROOM_TEMP  "Light: custom colour temp (K)"        6500.0 2000.0 10000.0 100.0
#pragma parameter DC_SPILL      "Light: TV light spill"                0.5 0.0 2.0 0.05
#pragma parameter DC_GLASS_LIFT "Light: room light on the glass"       0.3 0.0 1.0 0.05

struct ScreenRect { vec2 center; vec2 half_size; float aspect; vec2 curvature; float corner; };

// Reconstruct the shared rect. output_aspect = viewport width/height.
ScreenRect dc_get_rect(float output_aspect)
{
    ScreenRect r;
    r.aspect      = dcp.DC_ASPECT;
    r.curvature   = vec2(dcp.DC_CURVE_X, dcp.DC_CURVE_Y);   // per-axis barrel
    r.corner      = dcp.DC_CORNER;
    r.half_size.y = 0.5 * dcp.DC_SCALE;
    r.half_size.x = r.half_size.y * r.aspect / output_aspect;
    r.center      = vec2(dcp.DC_POS_X, dcp.DC_POS_Y);
    return r;
}

// Curved faceplate. The glass is a patch of a sphere (x and y radii may differ: a Trinitron is curved
// across only), and the raster is laid out evenly in DEFLECTION ANGLE, as the yoke sweeps it. Looking at the
// set from the front, a point at flat offset c (tube coords, [-0.5,0.5]) lies on the glass at height
// z = sqrt(1 - s.x^2 c.x^2 - s.y^2 c.y^2) (s = 1/radius) and is hit by the beam deflected by tan = c/z per axis.
// Normalising that by its value at the middle of each edge keeps the whole raster on the glass: the picture
// bows outward, the edge midpoints stay put, the corners pull in. Closed form both ways (dc_uncurve).
// k (DC_CURVE_*) -> s^2: about 10k for small k (a gentle barrel), saturating at 2 so the glass always spans the
// tube's corners.
vec2 dc_curve_s2(vec2 k){ return 10.0*k / (1.0 + 5.0*k); }
vec2 dc_curve(vec2 uv, vec2 k)                         // flat display coord -> raster coord, both [0,1]
{
    vec2 s2 = dc_curve_s2(k), c = uv - 0.5;
    float z = sqrt(max(1.0 - dot(s2, c*c), 1e-4));
    vec2 t_edge = 0.5 / sqrt(1.0 - 0.25*s2);           // deflection at the edge midpoints
    return 0.5 + 0.5 * (c / z) / t_edge;
}
vec2 dc_uncurve(vec2 ruv, vec2 k)                      // raster coord -> flat display coord (the inverse)
{
    vec2 s2 = dc_curve_s2(k);
    vec2 t = (ruv - 0.5) * 2.0 * (0.5 / sqrt(1.0 - 0.25*s2));
    return 0.5 + t / sqrt(1.0 + dot(s2, t*t));
}
// Viewport coord -> screen coord [0,1]; `inside` = 1 within the (curved) screen.
vec2 dc_vp_to_screen(vec2 vp, ScreenRect r, out float inside)
{
    vec2 p  = (vp - r.center) / r.half_size;            // [-1,1] in rect
    vec2 uv = p * 0.5 + 0.5;                            // [0,1] flat rect coord
    vec2 cuv = dc_curve(uv, r.curvature);               // the whole raster on the curved glass
    inside = (cuv.x >= 0.0 && cuv.x <= 1.0 && cuv.y >= 0.0 && cuv.y <= 1.0) ? 1.0 : 0.0;
    return cuv;
}

// Rounded-rect coverage of a screen-space coord (soft edge = `sharp`).
float dc_corner_mask(vec2 sp, float aspect, float corner, float sharp)
{
    vec2 p = abs(sp * 2.0 - 1.0);
    p.x *= aspect;
    vec2 d = p - (vec2(aspect, 1.0) - corner);
    float sd = length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0) - corner;
    return 1.0 - smoothstep(-sharp, sharp, sd);
}

// ---- Scene light, shared by every pass that draws lit art (bezel, frame, background, foreground).
//      The art is authored under a neutral reference light; dc_room_rgb() is the factor to multiply
//      its LINEAR colour by. DC_ROOM_LIGHT is a perceptual slider (intensity = x^2, 1 = as authored).
vec3 dc_s2l(vec3 c){ c = max(c, vec3(0.0)); return mix(c/12.92, pow((c + 0.055)/1.055, vec3(2.4)), vec3(greaterThan(c, vec3(0.04045)))); }
vec3 dc_l2s(vec3 c){ c = max(c, vec3(0.0)); return mix(c*12.92, 1.055*pow(c, vec3(1.0/2.4)) - 0.055, vec3(greaterThan(c, vec3(0.0031308)))); }
// black-body colour (display-referred, 0-1) — Tanner Helland's fit, K in [1000, 40000]
vec3 dc_kelvin(float K)
{
    float t = clamp(K, 1000.0, 40000.0) / 100.0;
    float r = (t <= 66.0) ? 255.0 : 329.698727446 * pow(t - 60.0, -0.1332047592);
    float g = (t <= 66.0) ? 99.4708025861 * log(t) - 161.1195681661 : 288.1221695283 * pow(t - 60.0, -0.0755148492);
    float b = (t >= 66.0) ? 255.0 : ((t <= 19.0) ? 0.0 : 138.5177312231 * log(t - 10.0) - 305.0447927307);
    return clamp(vec3(r, g, b) / 255.0, 0.0, 1.0);
}
vec3 dc_room_rgb()
{
    float x = clamp(dcp.DC_ROOM_LIGHT, 0.0, 1.0);
    float K = dcp.DC_ROOM_TEMP; vec3 shift = vec3(1.0);
    int type = int(dcp.DC_ROOM_TYPE + 0.5);
    if (type == 1) K = 2700.0;                                               // incandescent bulb
    if (type == 2) { K = 6200.0; shift = vec3(0.82, 1.0, 0.92); }             // fluorescent tube: mercury/phosphor green spike
    if (type == 3) K = 6500.0;                                               // daylight
    vec3 tint = dc_s2l(dc_kelvin(K)) / dc_s2l(dc_kelvin(6500.0));
    return x*x * sqrt(tint) * shift;                  // the eye half-adapts to the colour, not to the fluorescent cast
}
// lit art: display-referred colour as authored -> under the current room light (+ extra light, linear)
vec3 dc_light(vec3 c, vec3 extra) { return dc_l2s(dc_s2l(c) * (dc_room_rgb() + extra)); }
