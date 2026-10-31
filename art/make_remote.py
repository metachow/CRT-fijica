"""Standalone prop: a cheap 2000s 'universal remote' (万能遥控器) replicated from a period reference photo.
Drawn top-down, IR end UP, in REFERENCE units = px of the upright 2x reference with the body's top-left
at (0, 0) (body 290 x 1026 ~ a 21 cm remote). build() scales it. Brand/model are invented (BRAND/MODEL).
Also provides bag(): the protective plastic sleeve, on the same canvas, for the scene to lay over it.
Output (standalone run): out/remote.png + out/remote_preview.png."""
import math
import numpy as np
import skia
from common import *

BRAND = "HONGWEI"
MODEL = "RM-168C"
BW, BL = 290, 1026             # body width / length (reference units)
THICK = 75                     # body thickness at the battery end (~1.6 cm); the IR end is thinner (wedge)
THICK_IR = .80                 # IR-end thickness as a fraction of THICK
KEY_H = 9                      # how far the rubber keys stand proud of the face (~2 mm: low, pillowy rubber)
# where the scene's key light (upper left on screen) comes from, in face coords: lying IR-end-left in the room,
# +x (the body's far long side) is screen-up and -y (the IR end) screen-left. Keys are lit and shadowed for that.
LX, LY = .8, -.6
GREY = (168, 168, 171)
BLUE = (50, 94, 214)
GREEN = (36, 186, 86)


def latin(size, bold=True, italic=False):
    st = skia.FontStyle(700 if bold else 400, skia.FontStyle.kNormal_Width,
                        skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant)
    f = skia.Font(skia.Typeface.MakeFromName("Arial", st), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def shade(rgb, k):
    return C(*[int(np.clip(v * k, 0, 255)) for v in rgb])


def body_path():
    """Slight taper toward the battery end, which closes in a U."""
    p = skia.Path()
    p.moveTo(0, 36)
    p.quadTo(0, 0, 40, 0)
    p.lineTo(BW - 40, 0)
    p.quadTo(BW, 0, BW, 36)
    p.lineTo(BW - 12, 870)
    p.cubicTo(BW - 12, 990, BW * .5 + 70, BL, BW * .5, BL)
    p.cubicTo(BW * .5 - 70, BL, 8, 990, 8, 870)
    p.close()
    return p


# ------------------------------------------------------------------ glossy rubber keys
_KEYS = []                     # outline of every key drawn, so the scene can extrude them separately


def _key(path):
    _KEYS.append(skia.Path(path))


def key_oval(c, cx, cy, rx, ry, rgb, label="", lsize=24, lcol=C(255, 255, 255), lfont=None):
    r = rect(cx - rx, cy - ry, cx + rx, cy + ry)
    _key(skia.Path().addOval(r))
    _seat(c, skia.Path().addOval(r))
    c.drawOval(r, paint(shader=rad(cx + LX * rx * .35, cy + LY * ry * .35, max(rx, ry) * 1.7,
                                    [shade(rgb, 1.22), shade(rgb, 1.0), shade(rgb, .6)], [0, .45, 1])))
    c.drawOval(r, paint(shade(rgb, .45), stroke=1.4))
    # glossy rubber: a crescent of light along the rim facing the lamp
    c.drawOval(rect(cx + rx * .25, cy - ry * .78, cx + rx * .82, cy + ry * .55), paint(C(255, 255, 255, 62), blur=2.2))
    if label:
        f = lfont or latin(lsize)
        w = f.measureText(label)
        c.drawString(label, cx - w / 2, cy + lsize * .36, f, paint(lcol))


def key_pill(c, l, t, r, b, rgb, label="", lsize=14, lcol=C(30, 30, 30), lfont=None):
    rad_ = (b - t) / 2
    _key(skia.Path().addRRect(rrect(l, t, r, b, rad_)))
    _seat(c, skia.Path().addRRect(rrect(l, t, r, b, rad_)))
    c.drawRRect(rrect(l, t, r, b, rad_), paint(shader=lin(r, t, l, b, [shade(rgb, 1.22), shade(rgb, 1.0), shade(rgb, .64)], [0, .45, 1])))
    c.drawRRect(rrect(l, t, r, b, rad_), paint(shade(rgb, .45), stroke=1.3))
    c.drawRRect(rrect(r - (r - l) * .38, t + 2, r - 2, b - rad_ * .4, rad_ * .4), paint(C(255, 255, 255, 56), blur=1.8))
    if label:
        text_center(c, label, (l + r) / 2, (t + b) / 2 + lsize * .36, lfont or latin(lsize), paint(lcol))


def _seat(c, p):
    """The key sits in a hole in the face: a dark gap all round, plus its shadow thrown away from the light."""
    g = skia.Path(p); c.drawPath(g, paint(C(0, 0, 0, 190), stroke=4, blur=1.2))
    sh = skia.Path(p); sh.offset(-LX * 4, -LY * 4)
    c.drawPath(sh, paint(C(0, 0, 0, 170), blur=3))


def key_round(c, cx, cy, r, rgb=GREY, label="", lsize=12, lcol=C(30, 30, 30)):
    key_oval(c, cx, cy, r, r, rgb, label, lsize, lcol)


def label(c, s, cx, y, size=15):
    text_center(c, s, cx, y, font(size, "500"), paint(C(236, 236, 236)))


def chevron(c, cx, cy, s, up=True, col=C(250, 250, 250), w=5):
    p = skia.Path()
    k = -1 if up else 1
    p.moveTo(cx - s, cy - k * s * .5); p.lineTo(cx, cy + k * s * .5); p.lineTo(cx + s, cy - k * s * .5)
    pt = paint(col, stroke=w); pt.setStrokeCap(skia.Paint.kRound_Cap); pt.setStrokeJoin(skia.Paint.kRound_Join)
    c.drawPath(p, pt)


def tri(c, cx, cy, s, dirn, col):
    p = skia.Path()
    if dirn == "up":
        p.moveTo(cx, cy - s); p.lineTo(cx + s, cy + s * .6); p.lineTo(cx - s, cy + s * .6)
    elif dirn == "down":
        p.moveTo(cx, cy + s); p.lineTo(cx + s, cy - s * .6); p.lineTo(cx - s, cy - s * .6)
    elif dirn == "left":
        p.moveTo(cx - s, cy); p.lineTo(cx + s * .6, cy - s); p.lineTo(cx + s * .6, cy + s)
    else:
        p.moveTo(cx + s, cy); p.lineTo(cx - s * .6, cy - s); p.lineTo(cx - s * .6, cy + s)
    p.close(); c.drawPath(p, paint(col))


def rocker(c, cx, top, bot, rgb=GREY):
    """Peanut-shaped vol/ch rocker: two lobes joined by a waist."""
    r_lobe, r_waist = 30, 24
    p = skia.Path()
    p.addCircle(cx, top + r_lobe, r_lobe); p.addCircle(cx, bot - r_lobe, r_lobe)
    q = skia.Path(); q.addRRect(rrect(cx - r_waist, top + r_lobe, cx + r_waist, bot - r_lobe, 4))
    p = skia.Op(p, q, skia.PathOp.kUnion_PathOp)
    _key(p)
    _seat(c, p)
    c.drawPath(p, paint(shader=lin(cx + r_lobe, 0, cx - r_lobe, 0, [shade(rgb, 1.0), shade(rgb, 1.2), shade(rgb, .95), shade(rgb, .58)], [0, .25, .6, 1])))
    c.drawPath(p, paint(shade(rgb, .42), stroke=1.4))
    c.save(); c.clipPath(p, doAntiAlias=True)
    c.drawPaint(paint(shader=lin(0, top, 0, bot, [C(255, 255, 255, 70), C(255, 255, 255, 0), C(0, 0, 0, 40), C(255, 255, 255, 30), C(0, 0, 0, 60)], [0, .3, .5, .55, 1])))
    c.restore()


# ------------------------------------------------------------------ sections
def shell(c):
    bp = body_path()
    c.drawPath(bp, paint(shader=lin(0, 0, BW, 0, [C(54, 54, 58), C(30, 30, 33), C(22, 22, 24), C(20, 20, 22), C(40, 40, 44)], [0, .08, .4, .85, 1])))
    c.save(); c.clipPath(bp, doAntiAlias=True)
    # glossy sheen down the left shoulder + soft top highlight
    c.drawPaint(paint(shader=lin(0, 0, BW, 0, [C(255, 255, 255, 0), C(255, 255, 255, 22), C(255, 255, 255, 0)], [.02, .07, .16])))
    c.drawPaint(paint(shader=rad(BW * .3, 0, 360, [C(255, 255, 255, 18), C(255, 255, 255, 0)])))
    # matte lower panel behind the rockers, with a lit seam
    lp = skia.Path(); lp.moveTo(-10, 632); lp.quadTo(BW / 2, 612, BW + 10, 632); lp.lineTo(BW + 10, 782); lp.quadTo(BW / 2, 790, -10, 782); lp.close()
    c.drawPath(lp, paint(shader=lin(0, 620, 0, 790, [C(38, 38, 41), C(32, 32, 35), C(28, 28, 31)])))
    seam = skia.Path(); seam.moveTo(-10, 632); seam.quadTo(BW / 2, 612, BW + 10, 632)
    c.drawPath(seam, paint(C(10, 10, 10), stroke=2.5))
    seam.offset(0, 2.4); c.drawPath(seam, paint(C(110, 110, 116, 120), stroke=1.2))
    c.restore()
    c.drawPath(bp, paint(C(8, 8, 9), stroke=2))
    inner = skia.Path(bp); c.save(); c.clipPath(bp, doAntiAlias=True)
    c.drawPath(inner, paint(shader=lin(0, 0, BW, 0, [C(170, 170, 176, 130), C(120, 120, 126, 50), C(60, 60, 66, 0)], [0, .3, .7]), stroke=5))
    c.restore()


def top_rows(c):
    for x in (201, 221, 241):                                         # IR emitter windows
        c.drawCircle(x, 33, 3.4, paint(C(60, 60, 64)))
        c.drawCircle(x - .8, 32, 1.4, paint(C(150, 150, 156)))
    key_round(c, 54, 61, 14, GREY, "SET", 8)
    c.drawCircle(104, 61, 5.5, paint(C(20, 6, 6)))
    c.drawCircle(104, 61, 3.8, paint(shader=rad(103, 60, 5, [C(220, 70, 60), C(120, 16, 14)])))
    key_pill(c, 191, 48, 251, 78, GREEN, "POWER", 11, C(255, 255, 255))
    label(c, "设置键", 54, 93, 14)
    key_pill(c, 38, 102, 84, 126, GREY, "I/II", 13)
    key_round(c, 119, 114, 13, GREY, "S", 15)
    key_round(c, 168, 114, 13, GREY, "P.S", 9)
    key_pill(c, 206, 104, 251, 126, GREY)
    c.drawCircle(228.5, 115, 6.5, paint(C(40, 40, 40), stroke=1.6))     # sleep: clock glyph
    c.drawLine(228.5, 115, 228.5, 110.5, paint(C(40, 40, 40), stroke=1.4)); c.drawLine(228.5, 115, 232, 116.5, paint(C(40, 40, 40), stroke=1.4))
    for s, x in (("丽音", 56), ("伴音", 119), ("制式", 170), ("睡眠", 230)):
        label(c, s, x, 145, 14)


def number_pad(c):
    nf = latin(25)
    keys = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["--/-", "0", "⇄"]]
    for r, row in enumerate(keys):
        for k, s in enumerate(row):
            cx, cy = (61, 143, 224)[k], (164, 223, 280, 337)[r]
            if s == "⇄":
                key_oval(c, cx, cy, 27, 17, BLUE)
                for dy, d in ((-4, 1), (4, -1)):
                    c.drawLine(cx - 9, cy + dy, cx + 9, cy + dy, paint(C(255, 255, 255), stroke=2.4))
                    tri(c, cx + 10 * d, cy + dy, 4.5, "right" if d > 0 else "left", C(255, 255, 255))
            else:
                key_oval(c, cx, cy, 27, 17, BLUE, s, 15 if len(s) > 1 else 25, lfont=latin(15) if len(s) > 1 else nf)


def function_rows(c):
    for x, s in zip((48, 106, 166, 224), ("交换", "画中画", "正常", "选台")):
        key_round(c, x, 384, 12)
        c.drawRRect(rrect(x - 5, 380, x + 5, 388, 1.5), paint(C(60, 60, 62), stroke=1.2))
        label(c, s, x, 410, 13)
    key_round(c, 54, 430, 15, GREY, "V", 15)
    key_round(c, 218, 430, 15, GREY, "A", 15)
    key_round(c, 106, 433, 13); c.drawLine(100, 433, 112, 433, paint(C(30, 30, 30), stroke=2.6))
    key_round(c, 166, 433, 13)
    c.drawLine(160, 433, 172, 433, paint(C(30, 30, 30), stroke=2.6)); c.drawLine(166, 427, 166, 439, paint(C(30, 30, 30), stroke=2.6))
    text_center(c, "CH", 136, 428, latin(13), paint(C(236, 236, 236)))
    label(c, "图像", 51, 460, 14); label(c, "声音", 218, 460, 14)


def nav(c):
    cx, cy = 136, 507
    c.drawOval(rect(cx - 78, cy - 48, cx + 78, cy + 48), paint(C(70, 70, 76, 120), stroke=2))
    c.drawOval(rect(cx - 76, cy - 46, cx + 76, cy + 46), paint(shader=rad(cx, cy - 20, 90, [C(16, 16, 18), C(6, 6, 7)])))
    key_oval(c, cx, cy - 39, 15, 9, GREY); tri(c, cx, cy - 40, 4, "up", C(30, 30, 30))
    key_oval(c, cx, cy + 41, 15, 9, GREY); tri(c, cx, cy + 40, 4, "down", C(30, 30, 30))
    for side in (-1, 1):
        x0 = cx + side * 83
        p = skia.Path()
        p.addRRect(rrect(x0 - 13, cy - 30, x0 + 13, cy + 30, 13))
        key_pill_path(c, p, GREY, cx=x0)
        cp = skia.Path(); k = side
        cp.moveTo(x0 - k * 4, cy - 9); cp.lineTo(x0 + k * 4, cy); cp.lineTo(x0 - k * 4, cy + 9)
        pt = paint(C(250, 250, 250), stroke=4); pt.setStrokeCap(skia.Paint.kRound_Cap); pt.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawPath(cp, pt)
    key_pill(c, 108, 495, 164, 519, GREY, "菜单", 13, lfont=font(13, "700"))


def key_pill_path(c, p, rgb, cx):
    _key(p)
    _seat(c, p)
    b = p.getBounds()
    c.drawPath(p, paint(shader=lin(b.right(), 0, b.left(), 0, [shade(rgb, 1.0), shade(rgb, 1.2), shade(rgb, .62)], [0, .3, 1])))
    c.drawPath(p, paint(shade(rgb, .45), stroke=1.3))


def lower_rows(c):
    key_round(c, 52, 587, 12)
    c.drawRect(rect(47, 583, 57, 591), paint(C(50, 50, 52), stroke=1.3))
    label(c, "屏显", 52, 614, 13)
    key_pill(c, 104, 581, 168, 603, GREY, "电视/视频", 9, lfont=font(9, "700"))
    key_round(c, 211, 587, 14, GREY, "OK", 11)
    label(c, "完成", 211, 614, 13)
    rocker(c, 68, 634, 750)
    rocker(c, 196, 634, 750)
    c.drawLine(58, 659, 78, 659, paint(C(250, 250, 250), stroke=4.4)); c.drawLine(68, 649, 68, 669, paint(C(250, 250, 250), stroke=4.4))
    c.drawLine(58, 726, 78, 726, paint(C(250, 250, 250), stroke=4.4))
    text_center(c, "VOLUME", 68, 694, latin(5.5), paint(C(40, 40, 40)))
    chevron(c, 196, 660, 11, up=True)
    chevron(c, 196, 724, 11, up=False)
    key_round(c, 132, 676, 12)
    for a in range(0, 180, 45):                                       # mute: little asterisk
        v = math.radians(a)
        c.drawLine(132 - 6 * math.cos(v), 676 - 6 * math.sin(v), 132 + 6 * math.cos(v), 676 + 6 * math.sin(v), paint(C(50, 50, 52), stroke=1.4))
    label(c, "静音", 132, 706, 14)
    label(c, "音量", 68, 772, 14); label(c, "频道", 196, 772, 14)


def laurel(c, cx, side):
    """Wreath branch flanking the 超级版 badge: leaves along a gentle arc, pointing up-and-out."""
    col = C(150, 150, 154)
    for i in range(7):
        t = i / 6
        x = cx + side * (90 - 38 * t * t)
        y = 896 + 62 * t
        c.save(); c.translate(x, y); c.rotate(side * (-20 + 75 * t))
        c.drawOval(rect(-3.6, -9.5, 3.6, 9.5), paint(col))
        c.restore()
    p = skia.Path(); p.moveTo(cx + side * 92, 890); p.quadTo(cx + side * 88, 948, cx + side * 50, 962)
    c.drawPath(p, paint(col, stroke=1.4))


def branding(c):
    lx, ly = 56, 826
    m = skia.Path(); m.moveTo(lx, ly); m.lineTo(lx + 13, ly - 20); m.lineTo(lx + 26, ly); m.moveTo(lx + 7, ly - 6); m.lineTo(lx + 19, ly - 6)
    c.drawPath(m, paint(C(236, 236, 236), stroke=2.4))
    c.drawPath(skia.Path().addRect(rect(lx + 8, ly - 3, lx + 18, ly)), paint(C(236, 236, 236)))
    c.save(); c.translate(86, 826); c.skew(-.16, 0)
    c.drawString(BRAND, 0, 0, latin(26), paint(C(240, 240, 240)))
    c.restore()
    text_center(c, MODEL, 136, 852, latin(22, bold=False), paint(C(232, 232, 232)), spacing=1)
    text_center(c, "UNIVERSAL  REMOTE", 136, 873, latin(13, bold=False), paint(C(220, 220, 220)), spacing=.6)
    text_center(c, "万能遥控器", 136, 893, font(17, "700"), paint(C(232, 232, 232)), spacing=2)
    sf = font(27, "900")
    text_center(c, "超级版", 136, 926, sf, paint(C(20, 20, 20), stroke=5), spacing=2)
    text_center(c, "超级版", 136, 926, sf, paint(shader=lin(0, 902, 0, 928, [C(250, 250, 250), C(170, 170, 174)])), spacing=2)
    c.save(); c.translate(136, 948); c.skew(-.18, 0)
    text_center(c, "LCD • LED • HDTV", 0, 0, latin(15), paint(C(240, 240, 240)), spacing=1.2)
    c.restore()
    laurel(c, 136, -1); laurel(c, 136, 1)


def _canvas(scale, pad):
    w, h = int(np.ceil((BW + 2 * pad) * scale)), int(np.ceil((BL + 2 * pad) * scale))
    s = skia.Surface.MakeRaster(skia.ImageInfo.Make(w, h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    c = s.getCanvas(); c.clear(C(0, 0, 0, 0)); c.scale(scale, scale); c.translate(pad, pad)
    return s, c


def _snap(s):
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return a.astype(np.float32) / 255


def build(scale=1.0, pad=60):
    """Remote, top face. Returns (straight-alpha RGBA, origin = body top-left in image px)."""
    img, _, origin = build_layers(scale, pad)
    return img, origin


def build_layers(scale=1.0, pad=60):
    """As build(), plus a coverage mask of the keys (same canvas) so they can be raised off the face."""
    _KEYS.clear()
    s, c = _canvas(scale, pad)
    shell(c); top_rows(c); number_pad(c); function_rows(c); nav(c); lower_rows(c); branding(c)
    img = _snap(s)
    img[..., :3] *= (1 + .012 * grain(img.shape[0], img.shape[1], 71))[..., None]
    sm, cm = _canvas(scale, pad)
    for p in _KEYS:
        cm.drawPath(p, paint(C(255, 255, 255)))
    return img, _snap(sm)[..., 3], (pad * scale, pad * scale)


def bag(scale=1.0, pad=60, seed=5):
    """Clear PE sleeve a bit larger than the body: faint film, crinkle glints, heat-sealed end."""
    s, c = _canvas(scale, pad)
    rng = np.random.default_rng(seed)
    l, t, r, b = -34, -48, BW + 34, BL + 30
    p = skia.Path(); p.moveTo(l, t)
    for x in np.linspace(l, r, 6)[1:]:
        p.lineTo(x + rng.uniform(-6, 6), t + rng.uniform(-5, 5))
    for y in np.linspace(t, b, 9)[1:]:
        p.lineTo(r + rng.uniform(-8, 4), y)
    for x in np.linspace(r, l, 6)[1:]:
        p.lineTo(x, b + rng.uniform(-6, 6))
    for y in np.linspace(b, t, 9)[1:-1]:
        p.lineTo(l + rng.uniform(-4, 8), y)
    p.close()
    c.drawPath(p, paint(C(232, 238, 248, 7)))
    c.drawPath(p, paint(C(255, 255, 255, 55), stroke=2.4))
    for _ in range(7):                                                # a few soft crinkle glints, not scratches
        x0, y0 = rng.uniform(l, r), rng.uniform(t, b)
        ang = rng.uniform(-.4, .4) + (math.pi / 2 if rng.random() < .6 else 0)
        L = rng.uniform(80, 220)
        q = skia.Path(); q.moveTo(x0, y0)
        q.quadTo(x0 + L * .5 * math.cos(ang) + rng.uniform(-14, 14), y0 + L * .5 * math.sin(ang) + rng.uniform(-14, 14),
                 x0 + L * math.cos(ang), y0 + L * math.sin(ang))
        c.drawPath(q, paint(C(255, 255, 255, int(rng.uniform(12, 32))), stroke=rng.uniform(5, 10), blur=5))
    c.drawRect(rect(l, t, r, t + 16), paint(C(255, 255, 255, 60)))                     # heat seal
    for x in np.arange(l + 4, r, 9):
        c.drawLine(x, t + 2, x, t + 14, paint(C(255, 255, 255, 50), stroke=1.2))
    return _snap(s)


if __name__ == "__main__":
    import os
    from PIL import Image
    os.makedirs("out", exist_ok=True)
    img, _ = build(1.0)
    save_rgba(img, "out/remote.png")
    bg = Image.new("RGBA", (img.shape[1], img.shape[0]), (255, 153, 0, 255))
    bg.alpha_composite(Image.open("out/remote.png"))
    bg.convert("RGB").save("out/remote_preview.png")
    print("saved", img.shape)
