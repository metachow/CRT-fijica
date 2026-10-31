// =============================================================================
//  dc-composite.inc — the BEZEL + REFLECTION + COMPOSITE pass, shared by every look.
//  The look knobs below are compile-time (#ifndef-guarded): a pass file is just
//  `#version 450`, any #define overrides, then `#include "dc-composite.inc"`.
//    dc-composite.slang          default look (dark grey, the TM20 preset)
//    dc-composite-xinghui.slang  silver-beige consumer TV (the 星辉 room preset)
//  tools/crt-studio.html mirrors this pass line for line — change both together.
// =============================================================================
// Decoupled architecture — BEZEL + REFLECTION + COMPOSITE (final pass).
// Draws the bezel OUTSIDE the shared rect, composites the CRT texture INSIDE it,
// and casts an analytic reflection of the CRT onto the bezel. Reads ONLY the
// finished CRT texture + the contract — never CRT internals, no ray tracing.
//
// Model: the housing around the tube is a PROFILE, read from the tube outward: the black gap, the tube LIP (a
// rounded rim that rolls down into the tube), four flat sloped bezel FACES meeting at straight miter seams, the
// bezel's OUTER EDGE (rolling up onto the frame), the flat FRAME, and the frame's own edge (rolling away from the
// tube). Every part has a surface normal and ONE light shades them all (LIGHT_ANGLE / LIGHT_ELEV + AMBIENT,
// diffuse + a plastic gloss), so bright rims and dark rims follow the light instead of being painted on.
// Colours are what the plastic looks like FACE-ON (a surface looking straight at the viewer has shade 1).
// On top: the mirrored CRT reflection and the scene light below.
//
// Scene light (runtime DC_ROOM_* / DC_SPILL / DC_GLASS_LIFT, see dc-screen-layout.inc), in LINEAR light:
//   lit = authored colour x (room light x colour temp + TV spill)   — bezel, frame, background
//   + the picture's mirror reflection (emitted light, NOT dimmed by the room)
//   screen = picture + room light reflected off the glass (greys the blacks in daylight)
// Needs mipmap_input on this pass (the spill reads a heavily blurred picture from the mips).
layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
    vec4 OutputSize;
    vec4 OriginalSize;
    vec4 SourceSize;
    vec4 FinalViewportSize;
} global;

#include "dc-screen-layout.inc"

// Knob names of earlier versions would be silently ignored -> refuse them.
#if defined(MUL_TOP) || defined(MUL_BOT) || defined(MUL_SIDE) || defined(BZL_BRIGHT) || defined(BASE_VAL) || defined(BZL_OUTER_CORNER_RAD) || defined(FRM_OUTER_CORNER_RAD) || defined(CORNER_RAD) || defined(FRM_THICKNESS_SCALE_X)
#error "dc-composite: renamed knobs. MUL_TOP/BOT/SIDE + BZL_BRIGHT + BASE_VAL -> BZL_COLOR_VAL + LIGHT_ANGLE/LIGHT_ELEV/AMBIENT/BZL_SLOPE; *_OUTER_CORNER_RAD -> *_OUTER_CORNER (tube-height units); FRM_THICKNESS_SCALE_X -> FRM_WIDTH_X (absolute)"
#endif
#if defined(BZL_HL) || defined(INNER_EDGE_HL) || defined(BZL_INNER_EDGE_THICK) || defined(LIP_CORNER_PCT) || defined(INNER_EDGE_SHARP) || defined(INNER_EDGE_CORNER_FLOOR) || defined(INNER_EDGE_SHADOW) || defined(INNER_EDGE_SHADOW_W) || defined(CREASE_HL) || defined(FRM_INNER_EDGE_HL) || defined(FRM_INNER_EDGE_THICK) || defined(FRM_INNER_EDGE_SHADOW) || defined(OUTER_EDGE_SHADING) || defined(FRM_OUTER_EDGE_W)
#error "dc-composite: the painted-on rims are gone, rims are geometry now. BZL_HL/INNER_EDGE_HL/FRM_INNER_EDGE_HL/CREASE_HL -> BZL_GLOSS + BZL_SHINE; BZL_INNER_EDGE_THICK/INNER_EDGE_* -> LIP_WIDTH + LIP_ROLL; FRM_INNER_EDGE_* -> BZL_EDGE_W; OUTER_EDGE_SHADING/FRM_OUTER_EDGE_W -> FRM_EDGE_W + FRM_EDGE_ROLL"
#endif

// ---- UNITS: every length is a fraction of the TUBE HEIGHT (H), every angle is in degrees.

// --- Sizes ---
#ifndef BLACK_EDGE_W
#define BLACK_EDGE_W          0.005   // black band hugging the curved glass
#endif
#ifndef BZL_WIDTH
#define BZL_WIDTH             0.045   // sloped bezel, top & bottom: tube edge -> bezel outer edge
#endif
#ifndef BZL_WIDTH_X
#define BZL_WIDTH_X           0.045   // sloped bezel, left & right (the miter seams follow the corners)
#endif
#ifndef FRM_WIDTH
#define FRM_WIDTH             0.055   // flat frame, top & bottom: bezel outer -> frame outer
#endif
#ifndef FRM_WIDTH_X
#define FRM_WIDTH_X           0.0825  // flat frame, left & right
#endif
#ifndef BZL_OUTER_CORNER
#define BZL_OUTER_CORNER      0.0044  // bezel outer corner radius
#endif
#ifndef FRM_OUTER_CORNER
#define FRM_OUTER_CORNER      0.0024  // frame outer corner radius
#endif

// --- Material (as seen face-on) ---
#ifndef BZL_COLOR_HUE
#define BZL_COLOR_HUE   0.0     // 0-360
#endif
#ifndef BZL_COLOR_SAT
#define BZL_COLOR_SAT   0.0     // 0-100 (0 = neutral grey)
#endif
#ifndef BZL_COLOR_VAL
#define BZL_COLOR_VAL   0.20    // 0-1 brightness of the plastic
#endif
#ifndef BZL_NOISE
#define BZL_NOISE       0.10    // surface grain (moulded plastic)
#endif
#ifndef BZL_GLOSS
#define BZL_GLOSS       0.20    // plastic sheen: strength of the light's reflection (0 = matte)
#endif
#ifndef BZL_SHINE
#define BZL_SHINE       120.0   // ... and its tightness (low = broad satin sheen that also lifts flat faces,
                                // high = thin glints on the rounded edges only)
#endif

// --- Light (shared by every surface; match the background art's key light) ---
#ifndef LIGHT_ANGLE
#define LIGHT_ANGLE     90.0    // where the light comes FROM, on screen: 90 above, 0 right, 180 left, 135 upper-left
#endif
#ifndef LIGHT_ELEV
#define LIGHT_ELEV      60.0    // light's angle above the screen plane (90 = straight from the viewer -> faces even)
#endif
#ifndef AMBIENT
#define AMBIENT         0.35    // share of light that ignores direction (1 = all faces equal)
#endif
#ifndef BZL_SLOPE
#define BZL_SLOPE       30.0    // how steeply the bezel faces tilt into the tube (0 = flat)
#endif
// Large-scale falloff of the room light across the set (a nearby soft lamp, not the sun): the relative brightness
// gained per tube height moving right / up. Match the background art's own gradient, or the flat frame stops looking
// coplanar with the housing around it (brighter than it on one side = tilted towards the light, darker = sunk).
#ifndef LIGHT_GRAD_X
#define LIGHT_GRAD_X    0.0
#endif
#ifndef LIGHT_GRAD_Y
#define LIGHT_GRAD_Y    0.0
#endif

// --- Rounded edges of the profile (each one is lit through its own turning normal) ---
#ifndef LIP_WIDTH
#define LIP_WIDTH       0.006   // tube lip: width of the rounded rim between the black gap and the sloped face
#endif
#ifndef LIP_ROLL
#define LIP_ROLL        70.0    // ... how far it rolls down into the tube, deg (its normal at the gap)
#endif
#ifndef BZL_EDGE_W
#define BZL_EDGE_W      0.003   // bezel outer edge: width of the round-over from the sloped face onto the frame
#endif
#ifndef FRM_EDGE_W
#define FRM_EDGE_W      0.008   // frame outer edge: width of its round-over, away from the tube
#endif
#ifndef FRM_EDGE_ROLL
#define FRM_EDGE_ROLL   60.0    // ... how far it turns at the very edge, deg: > 0 the frame is a raised plate rolling
                                // away from the tube; < 0 it sits in a recess and the housing rises around it
#endif

// --- Corner seams (straight miter from the projected tube corner to the bezel outer corner) ---
#ifndef CORNER_FADE
#define CORNER_FADE      0.010  // softness of the face-colour change across the seam
#endif
#ifndef CREASE_W_IN
#define CREASE_W_IN      0.011  // seam width at the tube end (also carries extra reflection along the seam)
#endif
#ifndef CREASE_W_OUT
#define CREASE_W_OUT     0.002  // ... and at the outer end
#endif
#ifndef CREASE_STR
#define CREASE_STR       0.0    // occlusion in the seam's valley (the miter of a recess is concave; 0 = none)
#endif

// --- Frame (flat, outside the bezel) ---
#ifndef FRM_USE_INDEP_COLOR
#define FRM_USE_INDEP_COLOR    1      // 0 = same plastic as the bezel; 1 = FRM_COLOR_*
#endif
#ifndef FRM_COLOR_HUE
#define FRM_COLOR_HUE          0.0
#endif
#ifndef FRM_COLOR_SAT
#define FRM_COLOR_SAT          0.0
#endif
#ifndef FRM_COLOR_VAL
#define FRM_COLOR_VAL          0.30
#endif
#ifndef SHADOW_WIDTH
#define SHADOW_WIDTH           0.000  // drop shadow of the frame onto the background (0 = none)
#endif

// --- Background / black edge ---
#ifndef BLACK_EDGE_VAL
#define BLACK_EDGE_VAL  0.006   // black edge colour
#endif
#ifndef BG_BASE
#define BG_BASE         0.010   // procedural background (when DC_BG_ON = 0)
#endif

// --- TV light on the background art (its SpillMask says where; this says how strongly vs the bezel) ---
#ifndef BG_SPILL_GAIN
#define BG_SPILL_GAIN   5.0     // the room in front of the set catches the picture far better than the grazing bezel
#endif

// --- Glossy surface in the background art (SpillMask G, e.g. a varnished cabinet top) mirroring the picture.
//     A horizontal mirror seen by a level camera = a vertical flip about the line where it meets the set's face.
#ifndef GLOSS_STR
#define GLOSS_STR       0.0     // reflectance at the scene's grazing view (Fresnel; ~0.4 for varnish at 10 deg). 0 = off
#endif
#ifndef GLOSS_MIRROR_Y
#define GLOSS_MIRROR_Y  0.87    // the mirror line (the set's base on the surface), viewport fraction from the top
#endif
#ifndef GLOSS_STRETCH
#define GLOSS_STRETCH   1.0     // 1 = true geometry; >1 = seen from higher up (like the props' view cheat)
#endif
#ifndef GLOSS_BLUR
#define GLOSS_BLUR      0.15    // roughness: blur grows with the reflected distance
#endif

// --- Reflection of the picture on the bezel (screen-blended: weaker on light plastic, as on real sets) ---
#ifndef REFL_STR
#define REFL_STR        0.26    // overall strength
#endif
#ifndef REFL_FALLOFF
#define REFL_FALLOFF    0.042   // distance over which it fades away from the tube
#endif
#ifndef REFL_BLUR
#define REFL_BLUR       0.55    // how fast it blurs with that distance
#endif
#ifndef REFL_CORNER
#define REFL_CORNER     0.30    // extra mirrored picture carried along the miter seams
#endif

#pragma stage vertex
layout(location = 0) in vec4 Position;
layout(location = 1) in vec2 TexCoord;
layout(location = 0) out vec2 vTexCoord;
void main() { gl_Position = global.MVP * Position; vTexCoord = TexCoord; }

#pragma stage fragment
layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 FragColor;
layout(set = 0, binding = 2) uniform sampler2D Source;      // CRT layer output (viewport-space)
layout(set = 0, binding = 3) uniform sampler2D Background;  // device/console art BEYOND the frame
                                                           // (DC_BG_ON). The bezel embeds into it.
layout(set = 0, binding = 4) uniform sampler2D SpillMask;   // R = how much TV light each background pixel
                                                           // receives, G = glossy surface (mirrors the
                                                           // picture), baked with the art; black = none

// vTexCoord.y grows DOWNWARD in RetroArch; the light model works with y UP.
const float Y_UP = -1.0;

// HSV -> RGB (sat 0 -> grey = value). Hue in [0,1], sat in [0,1].
vec3 hsv2rgb(vec3 c){
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz)*6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
float hash21(vec2 p){ p = fract(p*vec2(123.34, 345.45)); p += dot(p, p+34.345); return fract(p.x*p.y); }
// signed distance to a centred rounded rect, q = |point| (first quadrant), b = half size
float sd_rrect(vec2 q, vec2 b, float rad){
    vec2 d = q - (b - rad);
    return length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0) - rad;
}
float coverage(float sd, float px){ return clamp(0.5 - sd/px, 0.0, 1.0); }   // 1 inside, 1-px AA

// The scene light, pointing TO it (y up on screen, z toward the viewer).
vec3 light_dir(){ float az = radians(LIGHT_ANGLE), el = radians(LIGHT_ELEV);
                  return vec3(cos(az)*cos(el), sin(az)*cos(el), sin(el)); }
// Matte brightness of a surface with normal n, relative to one looking straight at the viewer (= 1).
float face_shade(vec3 n){
    vec3 L = light_dir();
    return AMBIENT + (1.0 - AMBIENT) * max(dot(n, L), 0.0) / max(L.z, 0.05);
}
// The plastic's sheen on a surface with normal n (Blinn: half-vector between the light and the viewer), added on
// top of the colour. With a tight lobe (high BZL_SHINE) flat surfaces barely get any and the rounded edges whose
// normals sweep through the light's mirror direction show a thin glint, as on real glossy plastic.
float face_gloss(vec3 n){ vec3 h = normalize(light_dir() + vec3(0.0, 0.0, 1.0));
                          return BZL_GLOSS * pow(max(dot(n, h), 0.0), BZL_SHINE); }
// Normal of a surface sloping by `ang` degrees toward the 2D direction o.
vec3 tilt(vec2 o, float ang){ return vec3(o * sin(radians(ang)), cos(radians(ang))); }
// Unit direction AWAY from a centred rounded rect at q = |point| (first quadrant): the way its edge faces.
vec2 rrect_dir(vec2 q, vec2 b, float rad){
    vec2 d = q - (b - rad);
    if (d.x > 0.0 && d.y > 0.0) return normalize(d);
    return (d.x > d.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
}
// colour under the room light + extra (TV spill), plus the sheen (lit by the room light only), sRGB in/out
vec3 lit_plastic(vec3 c, vec3 extra, float gloss){
    vec3 room = dc_room_rgb();
    return dc_l2s(max(dc_s2l(c) * (room + extra) + gloss * room, 0.0));
}

// Where the CURVED tube corner lands on the FLAT bezel plane (H units, first quadrant): the inner end A of the
// straight miter seam A -> B (B = the bezel's outer corner). Exact: dc_uncurve of the raster corner.
vec2 seam_inner_A(vec2 curve, float aspect){
    return (dc_uncurve(vec2(1.0), curve) - 0.5) * vec2(aspect, 1.0);
}

// TV light spill: the picture lights what faces it. Colour (linear) = the nearby part of the picture blended
// with the whole picture (read from deep mips). The bezel/frame fade it by distance from the tube edge
// (H units); the background art carries its own baked receptivity (SpillMask).
vec3 spill_colour(vec2 vp, ScreenRect r){
    if (dcp.DC_SPILL <= 0.0) return vec3(0.0);
    float tube_px = 2.0 * r.half_size.y * global.OutputSize.y;
    vec2 p = (vp - r.center) / r.half_size;
    vec3 near_c  = textureLod(Source, r.center + clamp(p, -0.8, 0.8)*r.half_size, log2(max(0.25*tube_px, 1.0))).rgb;
    vec3 whole_c = textureLod(Source, r.center, log2(max(tube_px, 1.0))).rgb * 1.6;   // mip also averages the black surround
    return dcp.DC_SPILL * 1.5 * dc_s2l(0.5*near_c + 0.5*whole_c);
}

// The picture mirrored in a glossy horizontal surface of the background art (emitted light, linear).
// Blur grows with the reflected distance (rough varnish); a few rotated taps on the mips.
vec3 gloss_reflection(vec2 vp){
    float dy  = vp.y - GLOSS_MIRROR_Y;                              // > 0: below the mirror line
    if (dy <= 0.0) return vec3(0.0);
    float ty  = GLOSS_MIRROR_Y - GLOSS_STRETCH * dy;                // reflected point, above the line
    float rad = 0.003 + GLOSS_BLUR * GLOSS_STRETCH * dy;            // viewport-height units
    float lod = log2(max(0.5 * rad * global.OutputSize.y, 1.0));
    float rot = hash21(vp) * 6.2831853;
    vec3 acc = vec3(0.0);
    for (int k = 0; k < 8; k++){
        float t = (float(k) + 0.5) / 8.0, a = float(k) * 2.39996323 + rot;
        vec2 o = vec2(cos(a) * global.OutputSize.y * global.OutputSize.z, 1.4 * sin(a)) * sqrt(t) * rad;   // a bit taller than wide
        acc += textureLod(Source, vec2(vp.x, ty) + o, lod).rgb;
    }
    return dc_s2l(acc / 8.0) * GLOSS_STR;
}

// MIRRORED reflection: reflect the point back INTO the tube across the nearest edge/corner and
// sample there, blurred more with distance (Vogel golden-angle disk, per-pixel rotation ->
// grain-free). dob = distance from the black edge, crease = seam weight, band = inside-bezel.
vec3 reflection_layer(vec2 vp, ScreenRect r, float dob, float crease, float band, float px){
    if (dob <= 0.0 || band <= 0.001) return vec3(0.0);
    vec2 p = (vp - r.center) / r.half_size; vec2 cl = clamp(p, -1.0, 1.0);
    vec2 mir = cl - (p - cl);
    float blur = 0.02 + dob * REFL_BLUR;
    float rot  = hash21(vp) * 6.2831853;
    const int TAPS = 56; const float GA = 2.39996323;    // golden angle
    vec3 refl = vec3(0.0); float wsum = 0.0;
    for (int k = 0; k < TAPS; k++){
        float t  = (float(k)+0.5)/float(TAPS);
        float rr = sqrt(t)*blur; float ang = float(k)*GA + rot;
        vec2 mc  = clamp(mir + vec2(cos(ang), sin(ang))*rr, -1.0, 1.0);
        float wgt = exp(-2.2*t);
        refl += textureLod(Source, r.center + mc*r.half_size, 0.0).rgb * wgt; wsum += wgt;   // mip 0: Source has mips now
    }
    refl /= wsum;
    float fall  = exp(-dob / REFL_FALLOFF);
    float onset = smoothstep(0.0, 6.0*px, dob);          // few-px AA fade-in at the black edge
    return refl * (fall + crease*REFL_CORNER) * onset * band * REFL_STR;
}

vec3 bezel_layer(vec2 vp, ScreenRect r, vec2 segA)
{
    float aspect = r.aspect;
    float px = global.OutputSize.w / (2.0 * r.half_size.y);          // one output pixel, in H
    float ins; vec2 sp = dc_vp_to_screen(vp, r, ins);
    vec2 tcc = sp - 0.5;                                             // curved, [-0.5,0.5]
    vec2 flat_tcc = (vp - r.center) / r.half_size * 0.5;             // flat,   [-0.5,0.5]
    vec2 gc = abs(tcc)*vec2(aspect, 1.0);                            // curved, H units
    vec2 gf = abs(flat_tcc)*vec2(aspect, 1.0);                       // flat,   H units
    vec2 sgn = vec2(flat_tcc.x < 0.0 ? -1.0 : 1.0, flat_tcc.y*Y_UP < 0.0 ? -1.0 : 1.0);   // quadrant, y up

    // ---- distances (H): curved tube edge, flat bezel outer, flat frame outer ----
    vec2  tube_half = vec2(0.5*aspect, 0.5);
    float sd_tube  = sd_rrect(gc, tube_half, r.corner*0.5);
    vec2  bzl_half = tube_half + vec2(BZL_WIDTH_X, BZL_WIDTH);
    vec2  frm_half = bzl_half + vec2(FRM_WIDTH_X, FRM_WIDTH);
    float sd_bezel = sd_rrect(gf, bzl_half, BZL_OUTER_CORNER);
    float sd_frame = sd_rrect(gf, frm_half, FRM_OUTER_CORNER);
    float dob = sd_tube - BLACK_EDGE_W;                              // 0 at the black edge, + into the bezel
    float OUTSIDE_TUBE_EDGE = smoothstep(-1.5*px, 1.5*px, dob);
    float IN_BEZEL = coverage(sd_bezel, px);
    float IN_FRAME = coverage(sd_frame, px);

    // ---- the four faces, split by the straight miter seam A -> B ----
    vec2  segAB  = bzl_half - segA; float segL = max(length(segAB), 1e-4); vec2 segDir = segAB/segL;
    vec2  segRel = gf - segA;
    float across = segDir.x*segRel.y - segDir.y*segRel.x;            // > 0: top/bottom face side
    float seam_t = clamp(dot(segRel, segDir)/segL, 0.0, 1.0);        // 0 inner -> 1 outer
    float seam_w = mix(CREASE_W_IN, CREASE_W_OUT, seam_t);
    float crease = exp(-pow(abs(across)/max(seam_w, 1e-4), 2.0)) * IN_BEZEL;
    float tb   = smoothstep(-CORNER_FADE, CORNER_FADE, across);
    float up   = smoothstep(-0.006, 0.006, flat_tcc.y*Y_UP);
    float left = smoothstep(0.006, -0.006, flat_tcc.x);
    // each face's outward direction (away from the tube); the surface itself tilts the other way, into the tube
    vec2 o_tb = vec2(0.0, mix(-1.0, 1.0, up)), o_sd = vec2(mix(1.0, -1.0, left), 0.0);

    // ---- the profile's slope, from the tube outward: the lip rolls from LIP_ROLL (looking into the tube) up to
    //      the face's BZL_SLOPE, the face keeps it, the outer edge rounds it over to flat (0) onto the frame ----
    float t_lip  = clamp(dob / max(LIP_WIDTH, 1e-4), 0.0, 1.0);
    float t_edge = clamp(-sd_bezel / max(BZL_EDGE_W, 1e-4), 0.0, 1.0);          // 0 at the bezel's outer edge
    float slope  = mix(LIP_ROLL, BZL_SLOPE, sin(1.5707963*t_lip)) * smoothstep(0.0, 1.0, t_edge);
    // the lip hugs the tube's rounded corner: near the tube use the tube's own facing, further out the faces'
    vec2  o_lip  = rrect_dir(gc, tube_half, r.corner*0.5) * sgn;
    float lipw   = 1.0 - smoothstep(0.5, 1.0, t_lip);
    vec3  n_tb = tilt(-normalize(mix(o_tb, o_lip, lipw) + 1e-6), slope);
    vec3  n_sd = tilt(-normalize(mix(o_sd, o_lip, lipw) + 1e-6), slope);
    float shade = tb*face_shade(n_tb) + (1.0 - tb)*face_shade(n_sd);
    float gloss = tb*face_gloss(n_tb) + (1.0 - tb)*face_gloss(n_sd);
    // the miter is a small concave fillet: lit like the normal halfway between the two faces it joins
    vec3  n_fil = normalize(n_tb + n_sd);
    shade = mix(shade, face_shade(n_fil), crease) * (1.0 - CREASE_STR*crease);
    gloss = mix(gloss, face_gloss(n_fil), crease);

    // ---- colours: the plastic face-on, a moulded grain, the room light's falloff across the set ----
    float grain = hash21(floor(vp * global.OutputSize.xy)) - 0.5;
    vec3  base  = hsv2rgb(vec3(BZL_COLOR_HUE/360.0, BZL_COLOR_SAT/100.0, BZL_COLOR_VAL));
    float lgrad = max(1.0 + LIGHT_GRAD_X*flat_tcc.x*aspect + LIGHT_GRAD_Y*flat_tcc.y*Y_UP, 0.0);
    vec3  bezel_diffuse = base * (1.0 + BZL_NOISE*grain) * shade * lgrad;

    // ---- scene light: the room light + the TV's spill. The sloped bezel faces the tube and catches it directly;
    //      the flat frame lies in the screen's plane (the picture only shines forward), so like the housing art
    //      around it, it only gets what the background's SpillMask says (room bounce; none without a mask). ----
    vec3 spill_c = spill_colour(vp, r);
    vec3 spill = spill_c / (1.0 + pow(max(dob, 0.0) / 0.05, 2.0));
    vec3 flat_spill = (dcp.DC_BG_ON > 0.5) ? texture(SpillMask, vp).r * BG_SPILL_GAIN * spill_c : vec3(0.0);
    vec3 bezel_color = lit_plastic(bezel_diffuse, spill, gloss * lgrad);

    // ---- the picture's mirror image in the bezel, screen-blended (weaker on light plastic, as on real sets) ----
    vec3 refl = reflection_layer(vp, r, dob, crease, IN_BEZEL, px);
    bezel_color += refl * (1.0 - clamp(bezel_color, 0.0, 1.0));

    // ---- frame: flat, then its outer edge turns away from the tube by up to FRM_EDGE_ROLL ----
    vec3  frm_base = (FRM_USE_INDEP_COLOR != 0) ? hsv2rgb(vec3(FRM_COLOR_HUE/360.0, FRM_COLOR_SAT/100.0, FRM_COLOR_VAL)) : base;
    float t_frm = clamp(-sd_frame / max(FRM_EDGE_W, 1e-4), 0.0, 1.0);           // 0 at the frame's outer edge
    vec3  n_frm = tilt(rrect_dir(gf, frm_half, FRM_OUTER_CORNER) * sgn, FRM_EDGE_ROLL * (1.0 - sin(1.5707963*t_frm)));
    vec3  frame_color = lit_plastic(frm_base * (1.0 + 0.6*BZL_NOISE*grain) * face_shade(n_frm) * lgrad, flat_spill,
                                    face_gloss(n_frm) * lgrad);

    // ---- composite: tube black edge -> bezel -> flat frame -> background ----
    vec3 col = dc_light(vec3(BLACK_EDGE_VAL), spill);
    col = mix(col, bezel_color, OUTSIDE_TUBE_EDGE);
    col = mix(col, frame_color, 1.0 - IN_BEZEL);

    float frame_shadow = (SHADOW_WIDTH > 0.0) ? pow(1.0 - smoothstep(0.0, SHADOW_WIDTH, max(sd_frame, 0.0)), 2.0) : 0.0;
    vec3 bg = vec3(BG_BASE) * (0.80 + 0.4*(1.0 - length(vp - r.center)));
    if (dcp.DC_BG_ON > 0.5) bg = texture(Background, vp).rgb;      // device art beyond the frame
    bg *= 1.0 - 0.6*frame_shadow;
    bg = dc_light(bg, flat_spill);                                   // pre-lit art -> room light + TV spill
    if (dcp.DC_BG_ON > 0.5 && GLOSS_STR > 0.0) {                     // glossy surfaces mirror the picture
        float gls = texture(SpillMask, vp).g;
        if (gls > 0.002) bg = dc_l2s(dc_s2l(bg) + gls * gloss_reflection(vp));
    }

    return mix(col, bg, 1.0 - IN_FRAME);
}

void main()
{
    float out_aspect = global.OutputSize.x / global.OutputSize.y;
    ScreenRect r = dc_get_rect(out_aspect);
    float inside; vec2 sp = dc_vp_to_screen(vTexCoord, r, inside);
    vec2 segA = seam_inner_A(r.curvature, r.aspect);

    vec3 bez  = bezel_layer(vTexCoord, r, segA);
    vec3 crt  = textureLod(Source, vTexCoord, 0.0).rgb;
    // room light bounced off the glass + grey-green phosphor screen: lifts the blacks in a lit room
    crt = dc_l2s(dc_s2l(crt) + 0.02 * dcp.DC_GLASS_LIFT * dc_room_rgb() * vec3(0.92, 1.0, 0.96));

    // screen-edge mask — NOT gated by the boolean `inside` (that would hard-clip the corner AA).
    float scr = dc_corner_mask(sp, r.aspect, r.corner, 2.0*global.OutputSize.w);
    vec3 outp = mix(bez, crt, scr);

    // ±1 LSB TPDF dither: breaks the halation glow's 8-bit banding into imperceptible noise.
    vec2 dp = gl_FragCoord.xy;
    float tpdf = (hash21(dp) + hash21(dp + 41.7) - 1.0) / 255.0;
    outp += tpdf;

    FragColor = vec4(outp, 1.0);
}
