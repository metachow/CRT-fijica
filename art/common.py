"""Shared helpers for the Chinese CRT TV bezel graphics (4K canvas)."""
import numpy as np
import skia
from PIL import Image

W, H = 3840, 2160

# The CRT, its sloped bezel and the flat frame around it are drawn by the SHADER (decoupled/dc-composite), exactly
# like the TM20 preset: the art leaves this area as plain housing (no hole, no painted bezel). This is the single
# source for both the art and the shader's DC_* / width params (see dc_params.py).
SCREEN_CENTER = (1920, 930)    # px
TUBE_H = 1431                  # tube (4:3 content) height, px -> DC_SCALE
TUBE_ASPECT = 1.333
BZL_W, BZL_WX = 0.040, 0.040  # shader BZL_WIDTH / BZL_WIDTH_X (top-bottom / left-right), in tube heights
FRM_W, FRM_WX = 0.019, 0.019  # shader FRM_WIDTH / FRM_WIDTH_X


def shader_frame():
    """Outer edge of the shader's frame in px (l, t, r, b) — mirrors dc-composite's frm_half."""
    cx, cy = SCREEN_CENTER
    hh = .5 * TUBE_H * (1 + 2 * (BZL_W + FRM_W))
    hw = .5 * TUBE_H * (TUBE_ASPECT + 2 * (BZL_WX + FRM_WX))
    return cx - hw, cy - hh, cx + hw, cy + hh

# Real-world scale at the TV FACE. The cutout (2032 px) is the opening of a 29" 4:3 tube (~60 cm) -> ~34 px/cm.
# The set stands at the back edge of the cabinet top, so this is the scale of the wall plane; anything nearer
# the camera (VCD, remote, cabinet front) is bigger -> size props with make_bg.px_per_cm(depth), not by eye.
PX_PER_CM = 34

def _pick_family(*names):
    """First installed family; skia silently falls back to a non-CJK face otherwise."""
    for n in names:
        if skia.Typeface.MakeFromName(n, skia.FontStyle.Normal()).getFamilyName() == n:
            return n
    return names[0]


SANS = _pick_family("Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei")
SERIF = _pick_family("Noto Serif CJK SC", "Noto Serif SC", "SimSun")


def C(r, g, b, a=255):
    return skia.ColorSetARGB(int(a), int(r), int(g), int(b))


def surface():
    return skia.Surface.MakeRaster(
        skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))


def to_np(surf):
    """Snapshot -> float32 straight-alpha RGBA in [0,1]."""
    a = surf.makeImageSnapshot().toarray(
        colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return a.astype(np.float32) / 255.0


def save_rgba(arr, path):
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(path, optimize=True)


def over(top, bottom):
    """Straight-alpha 'over' compositing of float RGBA arrays."""
    ta, ba = top[..., 3:4], bottom[..., 3:4]
    oa = ta + ba * (1 - ta)
    rgb = (top[..., :3] * ta + bottom[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6)
    return np.concatenate([rgb, oa], axis=-1)


def rect(l, t, r, b):
    return skia.Rect.MakeLTRB(l, t, r, b)


def rrect(l, t, r, b, rad):
    return skia.RRect.MakeRectXY(rect(l, t, r, b), rad, rad)


def paint(color=None, shader=None, blur=0, stroke=0, aa=True, blend=None):
    p = skia.Paint(AntiAlias=aa)
    if color is not None:
        p.setColor(color)
    if shader is not None:
        p.setShader(shader)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke > 0:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
    if blend is not None:
        p.setBlendMode(blend)
    return p


def lin(x0, y0, x1, y1, colors, pos=None):
    return skia.GradientShader.MakeLinear(
        [skia.Point(x0, y0), skia.Point(x1, y1)], colors, pos)


def rad(cx, cy, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, colors, pos)


def font(size, weight="regular", family=SANS):
    st = {"regular": skia.FontStyle.Normal(), "bold": skia.FontStyle.Bold()}.get(weight)
    if st is None:
        st = skia.FontStyle(int(weight), skia.FontStyle.kNormal_Width, skia.FontStyle.kUpright_Slant)
    f = skia.Font(skia.Typeface.MakeFromName(family, st), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def text_center(canvas, s, cx, y, f, p, spacing=0.0):
    """Draw string centred at cx, optional extra letter spacing (px)."""
    if spacing == 0:
        w = f.measureText(s)
        canvas.drawString(s, cx - w / 2, y, f, p)
        return
    widths = [f.measureText(ch) for ch in s]
    total = sum(widths) + spacing * (len(s) - 1)
    x = cx - total / 2
    for ch, w in zip(s, widths):
        canvas.drawString(ch, x, y, f, p)
        x += w + spacing


def fbm(h, w, base, octaves=5, seed=0, persistence=0.5):
    """Value-noise fBm in roughly [-1,1]. base = feature size of first octave in px."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot, size = 1.0, 0.0, float(base)
    for _ in range(octaves):
        gh, gw = max(2, int(h / size) + 2), max(2, int(w / size) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray(g).resize((int(gw * size), int(gh * size)), Image.BICUBIC)
        a = np.asarray(im, np.float32)[:h, :w]
        out += amp * (a - 0.5) * 2
        tot += amp
        amp *= persistence
        size /= 2
        if size < 1:
            break
    return out / tot


def grain(h, w, seed=0):
    rng = np.random.default_rng(seed)
    return rng.standard_normal((h, w)).astype(np.float32)
