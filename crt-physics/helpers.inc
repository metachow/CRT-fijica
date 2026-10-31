// =============================================================================
//  helpers.inc — physical helper functions, included inside the fragment stage
//  of each pass (after `params` is in scope). Ported 1:1 from the Phase-1 single-pass prototype (in git history).
// =============================================================================

const vec3  LUMA     = vec3(0.2126, 0.7152, 0.0722);   // Rec.709
const float SQRT_2PI = 2.50662827;

// sRGB EOTF / inverse EOTF ----------------------------------------------------
vec3 to_linear(vec3 c) {
    bvec3 hi = greaterThan(c, vec3(0.04045));
    return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), vec3(hi));
}
vec3 to_srgb(vec3 c) {
    c = clamp(c, 0.0, 1.0);
    bvec3 hi = greaterThan(c, vec3(0.0031308));
    return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, vec3(hi));
}

// Stage 1: decode sRGB then apply gun gamma -> linear per-channel beam current.
vec3 gun_response(vec3 v) {
    return pow(to_linear(v), vec3(params.gamma_gun / 2.2));
}

// Stage 3a: current-dependent spot sigma (space-charge broadening), in the
// convolution axis' source-pixel units. base * (1 + k_sc * I^alpha_sc).
// `base` differs per axis: the vertical spot (sigma0) is tight for crisp
// scanlines; the horizontal spot (sigma_h) is wider to model video-bandwidth
// limiting, softening vertical pixel edges as a real CRT's analog line does.
float spot_sigma_base(float base, float I) {
    return base + base * params.k_sc * pow(max(I, 0.0), params.alpha_sc);
}
float spot_sigma(float I) { return spot_sigma_base(params.sigma0, I); }

// Stage 2d: beam deflection angle at normalized screen position uv in [0,1].
// theta = atan(distance-from-centre / gun-to-screen distance). Drives both the
// edge scanline elongation (Stage 3b) and the cos-law brightness falloff.
float deflection_theta(vec2 uv) {
    vec2 p = (uv - 0.5) * 2.0;                 // centre to [-1,1]
    return atan(length(p) / params.d_gun);
}

// Energy-conserving unit-area Gaussian weight at signed distance d [src px].
// Summing these WITHOUT normalizing by total weight is what keeps scanlines on
// flat fields: normalised weights would sum neighbouring rows to a constant and
// erase the dark gaps between scanlines.
float beam_weight(float d, float sigma) {
    return exp(-(d * d) / (2.0 * sigma * sigma)) / (sigma * SQRT_2PI);
}

// Stage 4: procedural phosphor mask. One soft RGB stripe centred at c, distance
// wrapped on the [0,3) triad ring so it tiles seamlessly.
float mask_stripe(float p, float c) {
    float d = abs(p - c);
    d = min(d, 3.0 - d);
    return smoothstep(0.8, 0.2, d);
}
// Per-channel RGB transmittance of one triad at horizontal position xt (in triad
// units, not yet fract'd) — the shared building block for all mask types.
vec3 rgb_triad(float xt) {
    float p = fract(xt) * 3.0;
    return vec3(mask_stripe(p, 0.5), mask_stripe(p, 1.5), mask_stripe(p, 2.5));
}
// Soft vertical window: ~1 across the cell, falling to 0 in the gap between rows
// of slots/dots. `edge` sets the gap softness. yp in [0,1).
float v_window(float yp, float edge) {
    return smoothstep(0.0, edge, yp) * smoothstep(1.0, 1.0 - edge, yp);
}
// Full mask transmittance at output-pixel position px, per mask_type. Slot and
// shadow masks add vertical structure (horizontal gaps) that aperture grille lacks.
vec3 phosphor_mask(vec2 px) {
    float xt = px.x / params.mask_pitch;          // horizontal position in triads
    vec3 m;
    if (params.mask_type < 0.5) {
        // Aperture grille: continuous vertical RGB stripes (no vertical structure).
        m = rgb_triad(xt);
    } else if (params.mask_type < 1.5) {
        // Slot mask: vertical RGB slots, brick-staggered (alternate triad columns
        // offset half a slot vertically).
        float slot_p = params.mask_pitch * 2.0;   // slot vertical period [out px]
        float yoff   = (mod(floor(xt), 2.0) < 1.0) ? 0.0 : 0.5;
        float yp     = fract(px.y / slot_p + yoff);
        m = rgb_triad(xt) * v_window(yp, 0.16);
    } else {
        // Shadow mask: RGB dot triads, hex-packed (alternate rows offset half a
        // triad horizontally so dots stagger).
        float row  = floor(px.y / params.mask_pitch);
        float xoff = (mod(row, 2.0) < 1.0) ? 0.0 : 0.5;
        float yp   = fract(px.y / params.mask_pitch);
        m = rgb_triad(xt + xoff) * v_window(yp, 0.22);
    }
    return mix(vec3(1.0), m, params.mask_strength);
}
