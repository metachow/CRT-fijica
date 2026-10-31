// =============================================================================
//  params.inc — shared physical parameters for the CRT-physics slang chain.
//  Included at the top of every pass (before the stage pragmas) so the whole
//  chain stays in sync. Defaults are the visually-tuned set from the Phase-1
//  single-pass prototype.
// =============================================================================

layout(push_constant) uniform Push
{
    float gamma_gun;      // Stage 1: gun cathode V-I power law (rel. to sRGB 2.2)
    float sigma0;         // Stage 3: min VERTICAL beam sigma at zero current [src px]
    float sigma_h;        // Stage 3: min HORIZONTAL beam sigma (bandwidth softening)
    float k_sc;           // Stage 3: space-charge broadening coefficient
    float alpha_sc;       // Stage 3: space-charge nonlinearity exponent
    float mask_type;      // Stage 4: 0=aperture grille, 1=slot mask, 2=shadow mask
    float mask_pitch;     // Stage 4: phosphor triad repeat [output px]
    float mask_strength;  // Stage 4: mask contrast (0 = off, 1 = opaque gaps)
    float e_sat;          // Stage 5a: phosphor saturation knee point
    float brightness;     // Stage 5: emission gain (η_0) — compensates mask loss
    float persist_r;      // Stage 5b: red afterglow per-frame decay (small; 0 = physical)
    float persist_g;      // Stage 5b: green afterglow per-frame decay (0..1)
    float persist_b;      // Stage 5b: blue afterglow per-frame decay (0..1)
    float halo_weight;    // Stage 6: fraction of emitted light scattered by glass
    float halo_spread;    // Stage 6: glass scatter Gaussian sigma [output px]
    float vignette;       // Stage 2d: edge brightness falloff (deflection cos law)
    float scan_mode;      // Stage 1.5: 0=progressive, 1=interlaced, 2=auto(by height)
    float interlace_off;  // Stage 1.5: off-field scanline brightness (flicker control)
    float d_gun;          // Stage 2d: gun-to-screen distance -> deflection angle
    float k_edge;         // Stage 3b: edge spot elongation strength
    float scan_gamma;     // Stage 3c: extra power-law on the vertical scanline
                          //           modulation (deepens dark lines; 1 = off)
} params;

#pragma parameter gamma_gun     "Gun gamma"                 2.25 1.8  3.0  0.05
#pragma parameter sigma0        "Beam sigma V [src px]"     0.14 0.10 0.9  0.01
#pragma parameter sigma_h       "Beam sigma H [src px]"     0.25 0.15 1.2  0.01
// k_sc = bloom AMOUNT (how much bright areas fatten). alpha_sc = bloom
// DURATION across brightness: lower alpha keeps the spot soft further into a
// fade, so a fading image stays soft and only sharpens in the last few frames
// (short "fade sharpening", like crt-lottes) without touching full-bright bloom.
#pragma parameter k_sc          "Space-charge k"            0.8  0.0  2.0  0.05
#pragma parameter alpha_sc      "Space-charge alpha"        0.4  0.2  1.0  0.05
// Mask type: 0 = aperture grille (vertical RGB stripes, Trinitron/PVM), 1 = slot
// mask (brick-staggered vertical slots, most consumer TVs), 2 = shadow mask (RGB
// dot triads, hex-packed). Slot/shadow have lower average transmittance -> dimmer;
// bump Brightness when switching to them.
#pragma parameter mask_type     "Mask type (0AG 1slot 2dot)" 0.0 0.0 2.0 1.0
#pragma parameter mask_pitch    "Mask pitch [out px]"       5.0  1.0  12.0 0.5
#pragma parameter mask_strength "Mask strength"             0.40 0.0  1.0  0.05
#pragma parameter e_sat         "Saturation knee"           1.5  0.5  4.0  0.1
// Emission gain (phosphor efficiency η_0). Compensates the brightness the
// aperture-grille mask removes, so calibrated white reaches full output.
#pragma parameter brightness    "Brightness (mask comp.)"   1.5  0.5  3.0  0.05
// Stage 5b temporal decay: per-frame afterglow decay factor (~60fps). Physically
// red decays fastest (~0 between frames) -> the "green trailing"; but a small red
// makes a WHITE object leave a whiter (less green/cyan) tail. persist_r 0 = pure
// physical green trail; raise it toward persist_g for a neutral white tail.
#pragma parameter persist_r     "Red afterglow"             0.02 0.0  0.95 0.01
#pragma parameter persist_g     "Green afterglow"           0.04 0.0  0.95 0.01
#pragma parameter persist_b     "Blue afterglow"            0.04 0.0  0.95 0.01
// Stage 6 halation: glass scatters a fraction (halo_weight) of the emitted light
// into a wide Gaussian glow (halo_spread). Scatter is proportional to emitted
// luminance, so pure-black regions stay black — no hazy-black artifact.
#pragma parameter halo_weight   "Halation weight"           0.08 0.0  0.30 0.01
#pragma parameter halo_spread   "Halation spread [out px]"  6.0  2.0  24.0 0.5
// Deflection: vignette darkens the edges (cos law). The screen's curvature and corners are the shared
// layout (DC_CURVE_X/Y, DC_CORNER in decoupled/dc-screen-layout.inc).
#pragma parameter vignette      "Vignette (edge falloff)"   0.12 0.0  0.60 0.02
// Stage 1.5 raster scan: 0=progressive (240p, all lines every frame), 1=force
// interlaced (480i, alternate fields), 2=auto (interlace when source >= 400 lines).
// Interlace flicker/combing emerge for free via the Pass 4 feedback (off-field
// lines show the previous field's decaying glow). Progressive is unchanged.
#pragma parameter scan_mode     "Scan (0=prog 1=int 2=auto)" 2.0 0.0 2.0 1.0
// In interlaced mode, off-field scanlines dim to this level instead of black.
// Real consumer-TV phosphors held the previous field's glow between fields, so
// off-field lines stayed bright -> only MILD flicker. 0 = harsh (only current
// field lit, strong flicker); ~0.6 = gentle flicker like a real TV; 1 = no flicker.
#pragma parameter interlace_off "Interlace off-field level"  0.6 0.0 1.0 0.05
// Deflection coupling: the beam is deflected further to reach screen edges, at
// angle theta = atan(dist_from_centre / d_gun). Smaller d_gun -> theta grows
// faster -> stronger edge effects. theta drives BOTH edge scanline elongation
// (k_edge, Stage 3b) AND the cos-law edge brightness falloff (Vignette, Stage 2d),
// so one physical distance couples geometry to beam and brightness.
#pragma parameter d_gun         "Gun distance (edge coupling)" 1.5 0.8 4.0 0.1
#pragma parameter k_edge        "Edge spot elongation"        0.4 0.0 1.0 0.05
// Stage 3c scanline contrast: an EXTRA power-law applied to the vertical scanline
// modulation envelope only. Physically this is the beam-current->luminance power
// law (gun/display gamma) acting on the scanline shape: the peak (env=1) is left
// untouched so the bright band stays plump/round, while the inter-scanline valley
// (env<1) is pushed darker -> deeper "horizontal dark lines" WITHOUT thinning the
// beam (unlike shrinking sigma0, which spikes the peak sub-pixel). 1 = off.
#pragma parameter scan_gamma    "Scanline contrast (gamma)"   1.25 1.0 3.0 0.05
